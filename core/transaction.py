import json

class Transaction:

    def __init__(self, fromAddress, toAddress, amount, fee=0):
        self.fromAddress = fromAddress
        self.toAddress = toAddress
        self.amount = amount
        self.fee = fee

    def as_dict(self):
        # Возвращает представление объекта в виде словаря
        return {
            'fromAddress': self.fromAddress,
            'toAddress': self.toAddress,
            'amount': self.amount,
            'fee': self.fee
        }

    def to_json(self):
        # Сериализует объект в строку JSON
        return json.dumps(self.as_dict())

    @classmethod
    def from_json(cls, json_str):
        # Создает и возвращает экземпляр класса из строки JSON
        data = json.loads(json_str)
        return cls(**data)