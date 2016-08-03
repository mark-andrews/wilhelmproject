from apps.core.utils.collections import Bunch

data_export = Bunch(
    dict(word_recognition_test_data = 'Word recognition test data',
         word_recall_test_data = 'Word recall test data',
         word_recall_option_length = 'Number of word recall slots')
)

# To calculate an F1 score, we need to know the number of relevant items. In a
# recall test as done here it is exactly half of the list of items in the
# wordlist recall memory test. In the case of the text recall memory test is as
# many as 250. To make the F1 value more easy to understand in text tests and
# more comparable across wordlist and text test, I am setting the value of the
# number of the relevant items at a fixed number.

recall_f1_score_number_of_relevant_items = 10.0
