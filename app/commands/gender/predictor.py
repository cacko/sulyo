from enum import Enum
import nltk
from nltk.corpus import names
import random
from pathlib import Path
from app import App


class Gender(Enum):
    M = "male"
    F = "female"
    U = "unknown"


class Predictor(object):

    __classifier = None
    __males: Path = None
    __females: Path = None
    _instance = None

    def __init__(self, males: Path, females: Path):
        self.__males = males
        self.__females = females
        featureset = self.__featureSets()
        random.shuffle(featureset)

        name_count = len(featureset)

        cut_point = int(name_count * 0.8)
        train_set = featureset[:cut_point]
        test_set = featureset[cut_point:]
        self.__classifier = self.__train(train_set)

    def __new__(cls, males, females, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def register(cls, app: App):
        cls(
            males=Path(__file__).parent / app.config.GENDER_MALE_NAMES,
            females=Path(__file__).parent / app.config.GENDER_FEMALE_NAMES,
        )

    def __featureSets(self):
        maleNames, femaleNames = names.words(self.__males.as_posix()), names.words(
            self.__females.as_posix()
        )

        result = []
        for nameTuple in maleNames:
            features = self.__nameFeatures(nameTuple[0])
            result.append((features, Gender.M))

        for nameTuple in femaleNames:
            features = self.__nameFeatures(nameTuple[0])
            result.append((features, Gender.F))

        return result

    def __train(self, train_set):
        return nltk.NaiveBayesClassifier.train(train_set)

    def __nameFeatures(self, name):
        name = name.upper()
        return {
            "last_letter": name[-1],
            "last_two": name[-2:],
            "last_is_vowel": (name[-1] in "AEIOUY"),
        }

    @classmethod
    def classify(cls, name) -> Gender:
        _self = cls._instance
        if not len(name):
            return Gender.U
        feats = _self.__nameFeatures(name)
        return _self.__classifier.classify(feats)
