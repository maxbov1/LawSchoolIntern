import pandas as pd
import sys

def parse_bar(filename):
    try:
        # Try reading with UTF-8 encoding
        bar = pd.read_csv(filename, encoding='utf-8')
    except UnicodeDecodeError:
        print(f"❌ UTF-8 decoding failed for {filename}, trying ISO-8859-1...")
        # Fallback to ISO-8859-1 (Latin-1) encoding
        bar = pd.read_csv(filename, encoding='ISO-8859-1')
        print(f"✅ Successfully read {filename} using ISO-8859-1 encoding.")

    # Clean up the bar data
    bar_clean = bar.loc[:, ["SID", "GraduationDate", "FirstTimeJuris"]]
    bar_clean['result'] = bar_clean['FirstTimeJuris'].str[2:]
    bar_clean['juris'] = bar_clean['FirstTimeJuris'].str[:2]
    bar_clean.drop(columns=['FirstTimeJuris'], inplace=True)

    # Drop rows with any missing values
    bar_clean = bar_clean.dropna(axis=0)

    # Save the cleaned data
    cleaned_filename = f'{filename}_clean.csv'
    bar_clean.to_csv(cleaned_filename, index=False)
    print(f"✅ Cleaned data saved as {cleaned_filename}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        parse_bar(filename)
    else:
        print("❌ Please provide the filename as an argument.")

