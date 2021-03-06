from items.models import Question, Answer

# Points earned/lost when prop. content is rated
POINTS_TABLE_RATED = {
    Question._meta.module_name: {-1: -2, 1: 5, 0: 0},
    Answer._meta.module_name: {-1: -2, 1: 10, 0: 0},
}

# Points earned/lost when rating content
POINTS_TABLE_RATING = {
    Question._meta.module_name: {-1: 0, 1: 0, 0: 0},
    Answer._meta.module_name: {-1: -1, 1: 0, 0: 0},
}
