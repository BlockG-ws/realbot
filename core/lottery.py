import dateutil.parser
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, \
    InlineKeyboardMarkup
from aiogram.utils.formatting import Bold

router = Router()

class LotteryForm(StatesGroup):
    title = State()
    description = State()
    type = State()
    number_of_winners = State()
    number_of_participants = State()
    end_time = State()
    send_to_chat = State()

async def handle_lottery_command(message: Message, state: FSMContext):
    if message.chat.type != 'private':
        await message.reply("请在私聊中使用此命令。")
        return
    await message.reply("现在创建抽奖活动。\n请输入抽奖的标题。一个好的抽奖标题可以吸引更多人参与！")
    await state.set_state(LotteryForm.title)

async def handle_draw_lottery(bot,lottery_id, chat_id):
    from adapters.db.lottery import end_lottery, get_lottery_info
    lottery = await get_lottery_info(chat_id=chat_id, lottery_id=lottery_id)
    participants = lottery.get('participants', [])
    winner_count = lottery.get('winner_count', 1)
    title = lottery.get('title', '抽奖活动')
    from helpers.rand import choose_random_winners
    winners_info = await choose_random_winners(participants=participants, number_of_winners=winner_count)
    winners = [str(w) for w in winners_info.get('winners', [])]

    await bot.send_message(chat_id=chat_id, text="抽奖活动达到了参与人数上限，正在开奖...")

    # 发送获奖者名单
    # TODO: 添加复现条件
    await bot.send_message(
        chat_id=chat_id,
        text= "🎉 抽奖活动结束！ 🎉\n\n" +
              Bold(title).as_html() +
              "获奖者名单：\n" +
              ", ".join(winners) + "\n\n" +
              "本抽奖基于 <a href=\"https://drand.love\">drand</a> 的第{round}次随机种子：{seed}\n"
              .format(
                  seed=winners_info['seed'],
                  round=winners_info['round'],
              )
    )

    # 标记抽奖为结束状态
    await end_lottery(chat_id=chat_id, lottery_id=lottery_id)

    # 更新数据库中的获奖者信息
    from adapters.db.lottery import update_lottery_info
    await update_lottery_info(chat_id=chat_id, lottery_id=lottery_id, lottery_data={'winners': winners_info['winners']})


@router.message(LotteryForm.title)
async def handle_lottery_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.reply("请输入抽奖的描述。如果不需要描述，请发送 /skip 。")
    await state.set_state(LotteryForm.description)

@router.message(LotteryForm.description)
async def handle_lottery_description(message: Message, state: FSMContext):
    if message.text != "/skip":
        await state.update_data(description=message.text)
    await message.reply("请输入获奖人数（必须为整数）。")
    await state.set_state(LotteryForm.number_of_winners)

@router.message(LotteryForm.number_of_winners)
async def handle_lottery_number_of_winners(message: Message, state: FSMContext):
    try:
        number_of_winners = int(message.text.strip())
        if number_of_winners <= 0:
            raise ValueError
    except ValueError:
        await message.reply("请输入一个有效的正整数作为获奖人数。")
        await state.set_state(LotteryForm.number_of_winners)
        return
    await state.update_data(number_of_winners=number_of_winners)
    await message.reply("获奖人数已设置为：{}".format(number_of_winners))
    await message.reply("请选择开奖触发条件：\n1. 固定时间结束\n2. 达到参与人数上限\n",
                        reply_markup=ReplyKeyboardMarkup(
                            keyboard=[
                                [
                                    KeyboardButton(text="固定时间"),
                                    KeyboardButton(text="达到参与人数"),
                                ]
                            ],
                            resize_keyboard=True,
                        ),
            )
    await state.set_state(LotteryForm.type)

@router.message(LotteryForm.type, F.text == "固定时间")
async def handle_lottery_type(message: Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.reply("请输入抽奖结束的时间，格式必须是 python 的 datetime 模块可以解析的格式，例如：2024-12-31 23:59:59",reply_markup=ReplyKeyboardRemove())
    await state.set_state(LotteryForm.end_time)

@router.message(LotteryForm.type, F.text == "达到参与人数")
async def handle_lottery_type_participants(message: Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.reply("请输入抽奖的最大参与人数（整数）。",reply_markup=ReplyKeyboardRemove())
    await state.set_state(LotteryForm.number_of_participants)

@router.message(LotteryForm.end_time)
async def handle_lottery_end_time(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        end_time = dateutil.parser.parse(text)
    except ValueError:
        await message.reply("时间格式不正确，请使用正确的格式重新输入。")
        await state.set_state(LotteryForm.end_time)
        return

    # 检查结束时间是否至少比当前时间晚
    from datetime import datetime, timedelta
    from dateutil import tz

    # Make end_time timezone-aware (assume local zone if none)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=tz.gettz("Asia/Shanghai"))

    now = datetime.now(tz=tz.gettz("Asia/Shanghai"))
    min_allowed = now + timedelta(minutes=10)
    if end_time < min_allowed:
        await message.reply("结束时间必须比当前时间晚至少10分钟，请输入更晚的时间。")
        await state.set_state(LotteryForm.end_time)
        return

    await message.reply("抽奖结束时间已设置为：{}".format(end_time.strftime("%Y-%m-%d %H:%M:%S")))
    await state.update_data(end_time=end_time.isoformat())
    await state.set_state(LotteryForm.send_to_chat)
    await message.reply(
        "请发送抽奖将要发送的目标 chat id，它必须是我已经加入的群组或者频道，否则抽奖消息将无法正确发送。\n你可以在群组或频道中发送 /info 命令来获取 chat_id。")


@router.message(LotteryForm.number_of_participants)
async def handle_lottery_number_of_participants(message: Message, state: FSMContext):
    try:
        max_participants = int(message.text.strip())
        if max_participants <= await state.get_value('number_of_winners'):
            raise ValueError
    except ValueError:
        await message.reply("请输入一个有效数字作为最大参与人数。")
        await state.set_state(LotteryForm.number_of_participants)
        return
    await state.update_data(max_participants=max_participants)
    await message.reply("最大参与人数已设置为：{}".format(max_participants))
    await state.set_state(LotteryForm.send_to_chat)
    await message.reply(
        "请发送抽奖将要发送的目标 chat id，它必须是我已经加入的群组或者频道，否则抽奖消息将无法正确发送。\n你可以在群组或频道中发送 /info 命令来获取 chat_id。")

@router.message(LotteryForm.send_to_chat)
async def handle_lottery_send_to_chat(message: Message, state: FSMContext):
    try:
        chat_id = int(message.text.strip())
    except ValueError:
        await message.reply("请输入一个有效的 chat_id（整数）。")
        await state.set_state(LotteryForm.send_to_chat)
        return
    data = await state.get_data()
    db_schema = data.copy()
    if db_schema["type"] == "固定时间":
        db_schema["max_participants"] = None
        db_schema["type"] = "time"
    elif db_schema["type"] == "达到参与人数":
        db_schema["type"] = "participants"
        db_schema["end_time"] = None
    try:
        lottery_msg = await message.bot.send_message(
            chat_id=chat_id,
            text=("🎉 抽奖活动已创建！ 🎉\n\n"
                  "标题：{title}\n"
                  "描述：{description}\n"
                  "类型：{type}\n"
                  "获奖人数：{number_of_winners}\n"
                  "最大参与人数：{max_participants}\n"
                  "结束时间：{end_time}\n\n"
                  "点击下方按钮参与抽奖！").format(
                      title=data.get("title"),
                      description=data.get("description", "无"),
                      number_of_winners=data.get("number_of_winners"),
                      type=data.get("type"),
                      max_participants=data.get("max_participants", "不限"),
                      end_time=data.get("end_time", "不限"),
                  )
        )
    except Exception as e:
        await message.reply(f"无法发送消息到指定的 chat id，请确保我是该聊天的成员，然后重试。\n错误信息：{e}")
        await state.set_state(LotteryForm.send_to_chat)
        return
    await message.reply("抽奖活动已成功发布")
    from adapters.db.lottery import save_lottery_info
    lottery_id = await save_lottery_info(chat_id=chat_id, lottery_data=db_schema)
    if db_schema["type"] == "time":
        from adapters.scheduler.lottery import start_lottery_job
        await start_lottery_job(lottery_id=lottery_id, chat_id=chat_id)
    if lottery_id:
        join_button = InlineKeyboardButton(text="参与抽奖", callback_data=f"join-lottery:{lottery_id}")
        join_markup = InlineKeyboardMarkup(inline_keyboard=[[join_button]])
        await lottery_msg.edit_reply_markup(reply_markup=join_markup)
    await state.clear()

@router.callback_query(lambda c: c.data.startswith('join-lottery:'))
async def handle_join_lottery(callback_query):
    lottery_id = int(callback_query.data.split(':')[1])
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    from adapters.db.lottery import get_lottery_info, update_lottery_info
    lottery = await get_lottery_info(chat_id=callback_query.message.chat.id, lottery_id=lottery_id)
    if not lottery or lottery.get('is_ended'):
        await callback_query.answer("该抽奖活动已结束。", show_alert=False)
        return
    participants = lottery.get('participants', [])
    if len(participants) == lottery.get('max_participants', float('inf')):
        await handle_draw_lottery(callback_query.message.bot,lottery_id, chat_id=chat_id)
    if user_id in participants:
        await callback_query.answer("你已经参与了该抽奖活动。", show_alert=False)
        return
    participants.append(user_id)
    await update_lottery_info(chat_id=callback_query.message.chat.id, lottery_data={'participants': participants}, lottery_id=lottery_id)
    await callback_query.answer("你已成功参与抽奖！祝你好运！", show_alert=False)