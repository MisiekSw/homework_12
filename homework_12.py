from collections import UserDict
from datetime import timedelta, datetime
import pickle


class Field:
    def __init__(self, value=None):
        self._value = None
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self.validate(new_value)
        self._value = new_value

    def validate(self, value):
        pass


class Name(Field):
    pass


class Phone(Field):
    def validate(self, value):
        if not value or not isinstance(value, str) or not value.isdigit():
            raise ValueError("Numer nie może być pusty i musi zawierać same cyfry.")


class Birthday(Field):
    def __init__(self, value=None):
        super().__init__(value)
        self.year, self.month, self.day = self.parse_date(value)

    def parse_date(self, value):
        if value:
            try:
                date_obj = datetime.strptime(value, "%Y-%m-%d")
                return date_obj.year, date_obj.month, date_obj.day
            except ValueError:
                raise ValueError("Niepoprawny format. Użyj YYYY-MM-DD.")
        return None, None, None


class Record:
    def __init__(self, name, phone, birthday=None):
        self.name = Name(name)
        self.phones = [Phone(phone)]
        self.birthday = None
        if birthday is not None:
            self.birthday = Birthday(birthday)

    def add_phone(self, phone):
        new_phone = Phone(phone)
        self.phones.append(new_phone)

    def remove_phone(self, phone):
        if phone in self.phones:
            self.phones.remove(phone)

    def edit_phone(self, old_phone, new_phone):
        if old_phone in self.phones:
            index = self.phones.index(old_phone)
            self.phones[index] = Phone(new_phone)

    def days_to_birthday(self):
        if self.birthday and all(
            [self.birthday.year, self.birthday.month, self.birthday.day]
        ):
            today = datetime.now()
            next_birthday = datetime(today.year, self.birthday.month, self.birthday.day)
            if today > next_birthday:
                next_birthday = datetime(
                    today.year + 1, self.birthday.month, self.birthday.day
                )
            days_left = (next_birthday - today).days
            return days_left
        else:
            return None


class AddressBook(UserDict):
    def __init__(self):
        super().__init__()

    def save_to_file(self, filename):
        with open(filename, "wb") as file:
            pickle.dump(self.data, file)

    def load_from_file(self, filename):
        try:
            with open(filename, "rb") as file:
                self.data = pickle.load(file)
        except FileNotFoundError:
            print("Plik nie istnieje. Książka adresowa została zainicjowana jako pusta")
        except Exception as e:
            print(f"Błąd podczas wczytywania pliku: {e}")

    def __iter__(self):
        return iter(self.data.values())

    def search_records(self, criteria):
        result = []
        for record in self.values():
            match = any(
                str(
                    getattr(record, field, None).lower().startswith(str(value).lower())
                    for field, value in criteria.items()
                )
            )
            if match:
                result.append(record)
        return result


class AssistantBot:
    def __init__(self):
        self.contacts = {}

    def get_first_n_records(self, n):
        record_iterator = iter(self.contacts.values())
        return [next(record_iterator) for _ in range(n)]

    def input_error(func):
        def errors(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyError:
                return "Wprowadź nazwę użytkownika."
            except ValueError:
                return "Podaj nazwę, telefon."
            except IndexError:
                return "Nie znaleziono kontaktu o podanej nazwie."

        return errors

    @input_error
    def handle_hello(self):
        return "How can I help you?"

    @input_error
    def handle_add(self, data):
        name, phone, *birthday = data.split()
        birthday = birthday[0] if birthday else None
        self.contacts[name] = Record(name, phone, birthday)
        return f"Kontakt {name} dodany z numerem telefonu {phone} i datą urodzin {birthday}."

    @input_error
    def handle_change(self, data):
        name, phone, birthday = data.split()
        if name in self.contacts:
            self.contacts[name] = Record(name, phone, birthday)
            return f"Zmieniono numer telefonu i/lub datę urodzin dla kontaktu {name} na {phone} i {birthday}."
        raise IndexError

    @input_error
    def handle_phone(self, name):
        if name in self.contacts:
            return f"Numer telefonu dla kontaktu {name}: {self.contacts[name].phones[0].value}."
        else:
            raise IndexError

    @input_error
    def handle_days_to_birthday(self, name):
        if name in self.contacts and self.contacts[name].birthday:
            days_left = self.contacts[name].days_to_birthday()
            return f"Liczba dni do urodzin dla kontaktu {name}: {days_left}."
        elif name in self.contacts and not self.contacts[name].birthday:
            return f"Kontakt {name} nie ma ustawionej daty urodzin."
        else:
            raise IndexError

    @input_error
    def handle_show_all(self):
        if not self.contacts:
            return "Brak zapisanych kontaktów."

        contact_info = [
            f"{name}: {record.phones[0].value if record.phones else 'Brak numeru telefonu'}, Birthday: {record.birthday.value if record.birthday else 'None'}"
            for name, record in self.contacts.items()
        ]

        return "\n".join(contact_info)

    @input_error
    def handle_show_n_records(self, data):
        try:
            n = int(data)
        except ValueError:
            raise ValueError("Podaj liczbę rekordów do wyświetlenia.")

        first_n_records = self.get_first_n_records(n)
        if not first_n_records:
            return "Brak dostępnych rekordów."

        return "\n".join(
            [
                f"{record.name.value}: {record.phones[0].value}, Birthday: {record.birthday.value if record.birthday else 'None'}"
                for record in first_n_records
            ]
        )

    def main(self):
        while True:
            user_input = input("Wprowadź polecenie: ").lower()

            if user_input in ["good bye", "close", "exit"]:
                print("Good bye!")
                break
            elif user_input == "hello":
                print(self.handle_hello())
            elif user_input.startswith("add"):
                print(self.handle_add(user_input[4:]))
            elif user_input.startswith("change"):
                print(self.handle_change(user_input[7:]))
            elif user_input.startswith("phone"):
                print(self.handle_phone(user_input[6:]))
            elif user_input.startswith("days to birthday"):
                print(self.handle_days_to_birthday(user_input[17:]))
            elif user_input == "show all":
                print(self.handle_show_all())
            elif user_input.startswith("show n records"):
                print(self.handle_show_n_records(user_input[14:]))
            elif user_input.startswith("search"):
                criteria = dict(item.split("=") for item in user_input[7:].split("."))
                search_result = self.contacts.search_records(criteria)
                if search_result:
                    print("Znalezione kontakty:")
                    for record in search_result:
                        print(
                            f"{record.name.value}: {record.phones[0].value}, Birthday: {record.birthday.value if record.birthday else 'None'}"
                        )
                else:
                    print("Brak pasujących kontaktów.")
            else:
                print("Nieznane polecenie. Spróbuj ponownie.")


if __name__ == "__main__":
    bot = AssistantBot()
    bot.contacts.load_from_file("address_book.pkl")
    bot.main()
