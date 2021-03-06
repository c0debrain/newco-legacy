from items.models import Question
from utils.vote import Vote


def main():
    for question in Question.objects.all():
        question.save()
        question.sort_related_answers()

    # Delete blank votes
    Vote.objects.filter(user__id__in=[2, 6]).delete()

if __name__ == "__main__":
    main()
