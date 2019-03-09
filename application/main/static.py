# static.py
class ClassGrades:

    def __init__(self, **kwargs):
        self.grades = kwargs.get('grades')

    @classmethod
    def from_csv(cls, **kwargs):
        return cls(**kwargs)

    @staticmethod
    def validate(grades):
        for g in grades:
            if g < 0 or g > 100:
                raise Exception()

cg = ClassGrades.from_csv(grades=[1,2,4])
print(cg.grades)
