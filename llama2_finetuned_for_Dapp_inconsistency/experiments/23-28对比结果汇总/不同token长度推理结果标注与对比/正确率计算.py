import pandas as pd

def calculate_accuracy_direct(data):
    total_samples = len(data)
    correct_samples = data['correct'].sum()
    accuracy = correct_samples / total_samples
    return accuracy

def calculate_accuracy_grouped(data):
    grouped_data = data.groupby('id')['correct'].all()
    total_groups = len(grouped_data)
    correct_groups = grouped_data.sum()
    accuracy = correct_groups / total_groups
    return accuracy

def main(excel_files):

    for excel_file in excel_files:
    
        print(excel_file)
        
        data = pd.read_excel(excel_file)
        

        direct_accuracy = calculate_accuracy_direct(data)
        print("direct a:", direct_accuracy)

        grouped_accuracy = calculate_accuracy_grouped(data)
        print("group a:", grouped_accuracy)

        print("\n")

if __name__ == "__main__":

    excel_files = ["4000token_out.xlsx","3000token_out.xlsx","2000token_out.xlsx"]
    main(excel_files)
