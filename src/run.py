from spider import AmazonScraper

if __name__ == "__main__":
    scraper = AmazonScraper()
    input_keywords = input("Enter keywords: ")
    input_file_name = input("Enter file name: ")

    if input_keywords == '' or input_file_name == '':
        print("Please enter keywords and file name")
        exit()
    else:
        if 'xlsx' not in input_file_name.split('.'):
            print("Please enter xlsx file format")
        else:
            scraper.run(input_keywords, input_file_name)