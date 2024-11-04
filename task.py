import copy
import pickle
from datetime import datetime, timedelta

# Декоратор для обробки помилок вводу
def input_error(func):
    """Декоратор для обробки помилок введення користувача."""
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Please give me proper value."
        except IndexError:
            return "Enter the argument for the command."
        except KeyError:
            return "Contact not found."
    return inner


class Field:
    def __init__(self, value):
        self.value = value


class Name(Field):
    def __init__(self, value):
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Invalid phone number format. It must be 10 digits.")
        super().__init__(value)

    @staticmethod
    def validate(value):
        return isinstance(value, str) and value.isdigit() and len(value) == 10


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def change_phone(self, old_phone, new_phone):
        for idx, phone in enumerate(self.phones):
            if phone.value == old_phone:
                self.phones[idx] = Phone(new_phone)
                return
        raise KeyError("Old phone not found.")

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        return f"Record(name={self.name.value}, phones={', '.join(p.value for p in self.phones)}, birthday={self.birthday.value if self.birthday else 'N/A'})"


class AddressBook:
    def __init__(self):
        self.contacts = []

    def add_record(self, record):
        self.contacts.append(record)

    def find(self, name):
        for record in self.contacts:
            if record.name.value.lower() == name.lower():
                return record
        return None

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.contacts:
            if record.birthday:
                birthday_this_year = record.birthday.value.replace(year=today.year)

                # If the birthday has already passed this year, move to next year
                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                # Check if the birthday is within the next 7 days
                if today <= birthday_this_year <= today + timedelta(days=7):
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "congratulation_date": birthday_this_year.strftime("%Y.%m.%d")
                    })

        return upcoming_birthdays


@input_error
def add_contact(args, book: AddressBook):
    """Додає контакт до адресної книги."""
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    """Змінює номер телефону для вказаного контакту."""
    if len(args) != 3:
        raise ValueError("Provide name, old phone, and new phone.")
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    record.change_phone(old_phone, new_phone)
    return "Phone number updated."


@input_error
def show_phone(args, book: AddressBook):
    """Показує номер телефону для вказаного контакту."""
    if len(args) != 1:
        raise ValueError("Missing arguments")
    name = args[0]
    record = book.find(name)
    if record:
        return f"{name}'s phone(s): {', '.join(p.value for p in record.phones)}"
    else:
        raise KeyError("Contact not found")


@input_error
def show_all(book: AddressBook):
    """Показує всі контакти."""
    if not book.contacts:
        return "No contacts found."
    return "\n".join(str(record) for record in book.contacts)


@input_error
def add_birthday(args, book: AddressBook):
    """Додає день народження для вказаного контакту."""
    name, birthday = args
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    record.add_birthday(birthday)
    return f"Birthday for {name} added."


@input_error
def show_birthday(args, book: AddressBook):
    """Показує день народження для вказаного контакту."""
    name = args[0]
    record = book.find(name)
    if record is None or record.birthday is None:
        return f"No birthday found for {name}."
    return f"{name}'s birthday is on {record.birthday.value.strftime('%d.%m.%Y')}."


@input_error
def birthdays(args, book: AddressBook):
    """Показує дні народження, які відбудуться протягом наступного тижня."""
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No upcoming birthdays this week."
    return "\n".join(f"{entry['name']}: {entry['congratulation_date']}" for entry in upcoming_birthdays)


def save_data(book, filename="addressbook.pkl"):
    """Серіалізує дані адресної книги у файл."""
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    """Завантажує дані адресної книги з файлу."""
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено


def parse_input(user_input):
    """Розбирає введений рядок на команду та аргументи."""
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


def main():
    book = load_data()  # Загружаємо адресну книгу при запуску
    print("Привіт! Я ваш асистент. Введіть 'hello' для початку.")

    while True:
        user_input = input("\nEnter a command: ").strip()
        command, *args = parse_input(user_input)

        if command in ["exit", "close"]:
            save_data(book)  # Зберігаємо адресну книгу при виході
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()