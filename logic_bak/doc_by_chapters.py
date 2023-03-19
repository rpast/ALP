""""
This file holds script for chunking the document into chapters
"""

    # print('Processing input document...')
    # # Currently we chop the document into chapters and then into smaller chunks
    # # TODO: User should decide if they want to chop the document into chapters or by page
    # #
    # # Logic for chapter capture
    # digit_word_rgx = r'^\d+(\.\d+)*\s[a-zA-Z]+.*$|Abstract'

    # # Load context document and grab chapter names
    # doc_name = input('Enter document name from input: ')

    # pdf_text = extract_text(prm.IN_PTH / doc_name)

    # chapters = utl.grab_chapters(pdf_text, matching_logic=2)

    # print('Script managed to capture the following chapters:')
    # for chapter in chapters:
    #     print(chapter)

    # # TODO: interface for selecting chapters to be used for text fragmentation. 
    # chapters = input('Enter chapters to be used for text fragmentation (separated by comma): ')
    # chapters = chapters.split(',')
    # chapters = [x.lower().strip() for x in chapters]
    # print(f"There are {len(chapters)} chapters in the document")

    # # Set a specific starting point of the document
    # # start = 'abstract'
    # start = input('Enter the starting point of the document: ')
    # start = start.lower().strip()

    # # TODO: make this text pre-processing function
    # # define the text to be parsed
    # text = [] 
    # for line in pdf_text.split('\n'):
    #     line = line.replace('\t', ' ')
    #     line = line.strip().lower()
    #     text.append(line)

    # text = ' '.join(text)
    # # replace newline and tab characters with space
    # text = text.replace('\n', '')
    # text = text.replace('\t', '')
    # text = re.sub(r'\s+', ' ', text)


    # # TODO: turn it into a function that will get triggered whe user decides to chop the document by chapter names

    # # Fragment the text according to the logic the user defined (currently - by chapters)

    # # join the end strings with | to form chapter end regex pattern
    # end_pattern = "|".join(chapters)

    # # match text between chapter and any end string
    # chapters_contents = {}
    # for string in chapters:

    #     pattern = rf"{string}(.*?)(" + end_pattern + "|$)"
    #     pattern = re.compile(pattern)



    #     # search for the pattern in the text
    #     match = pattern.search(text)

    #     # if there is a match, extract the text between string and any end-string
    #     if match:
    #         # get the first group of the match object, which is the text between given chapter and any end string
    #         result = match.group(1)

    #         # print or save or do whatever you want with the result
    #         chapters_contents[string] = result


    # #TODO: come up with test that checks if I grabbed all the chapters
    # fetched_chapters = [x for x in chapters_contents.keys()] 
    # # compare element wise fetched_chapters with chapters
    # missing_chapters = [x for x in chapters if x not in fetched_chapters]
    # print(f"Missing chapters: {missing_chapters}")

    # # Manually inspect some chapters
    # print('Printing the last 50 characters of the last chapter ', chapters_contents[chapters[-1]][-50:])