import nltk


def tokenize_file(filename):

    full_list = []

    with open(filename, 'r') as book_file:
        for file_line in book_file:
            line_list = file_line.split('.')
            for sentence in line_list:
                if sentence.strip():
                    full_list.append(sentence)

    return full_list

def tokenize_file_nltk(filename):

    with open(filename, 'r') as file:
        raw_string = file.read()

    return nltk.sent_tokenize(raw_string, language="russian")


