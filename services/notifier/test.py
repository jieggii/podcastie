from dataclasses import dataclass


@dataclass
class Test:
    x: list[str]


t = Test()
print(t)