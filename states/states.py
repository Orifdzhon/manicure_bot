from aiogram.fsm.state import State, StatesGroup

class BookingStates(StatesGroup):
    choosing_date  = State()
    choosing_slot  = State()
    entering_name  = State()
    entering_phone = State()
    confirming     = State()

class AdminStates(StatesGroup):
    main_menu      = State()
    add_day        = State()
    add_slot_date  = State()
    add_slot_time  = State()
    view_date      = State()
    manage_day     = State()
    delete_slot    = State()
    cancel_booking = State()
