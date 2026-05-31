from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from keyboards.keyboards import main_menu_kb, portfolio_kb, back_to_menu_kb, calendar_kb
from config import config

router = Router()

WELCOME_TEXT = (
    "👋 <b>Добро пожаловать!</b>\n\n"
    "Я бот для записи на маникюр 💅\n"
    "Выберите действие в меню ниже:"
)

PRICES_TEXT = (
    "💅 <b>Прайс-лист</b>\n\n"
    "• Френч — <b>1 000 ₽</b>\n"
    "• Квадрат — <b>500 ₽</b>\n\n"
    "По всем вопросам пишите в личные сообщения."
)


def _is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_kb(is_admin=_is_admin(message.from_user.id)),
    )


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_kb(is_admin=_is_admin(call.from_user.id)),
    )
    await call.answer()


@router.callback_query(F.data == "prices")
async def cb_prices(call: CallbackQuery):
    await call.message.edit_text(
        PRICES_TEXT, parse_mode="HTML", reply_markup=back_to_menu_kb()
    )
    await call.answer()


@router.callback_query(F.data == "portfolio")
async def cb_portfolio(call: CallbackQuery):
    await call.message.edit_text(
        "🖼 <b>Портфолио</b>\n\nПосмотрите мои работы на Pinterest:",
        parse_mode="HTML",
        reply_markup=portfolio_kb(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("cal:"))
async def cb_calendar_nav(call: CallbackQuery):
    """Навигация по месяцам в календаре."""
    _, year, month = call.data.split(":")
    await call.message.edit_reply_markup(
        reply_markup=calendar_kb(int(year), int(month))
    )
    await call.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()
