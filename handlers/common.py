# =============================================================
#  handlers/common.py — /start, главное меню, прайсы, портфолио
# =============================================================
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from keyboards.keyboards import main_menu_kb, portfolio_kb, back_to_menu_kb

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


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Приветствие и главное меню."""
    await state.clear()
    await message.answer(WELCOME_TEXT, parse_mode="HTML", reply_markup=main_menu_kb())


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await state.clear()
    await call.message.edit_text(WELCOME_TEXT, parse_mode="HTML", reply_markup=main_menu_kb())
    await call.answer()


@router.callback_query(F.data == "prices")
async def cb_prices(call: CallbackQuery):
    """Прайс-лист (без FSM)."""
    await call.message.edit_text(
        PRICES_TEXT, parse_mode="HTML", reply_markup=back_to_menu_kb()
    )
    await call.answer()


@router.callback_query(F.data == "portfolio")
async def cb_portfolio(call: CallbackQuery):
    """Портфолио — кнопка-ссылка."""
    await call.message.edit_text(
        "🖼 <b>Портфолио</b>\n\nПосмотрите мои работы на Pinterest:",
        parse_mode="HTML",
        reply_markup=portfolio_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    """Заглушка для неактивных кнопок."""
    await call.answer()
