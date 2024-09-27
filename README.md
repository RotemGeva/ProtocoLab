# ProtocoLab
ProtocoLab automates the verification of MRI protocol fields, enhancing testing efficiency and accuracy. With its intuitive interface, it simplifies protocol validation, ensuring consistency and improving MRI imaging quality.

## Features

- Automated verification of MRI protocols
- User-friendly WPF interface
- External tool functionality built in Python
- Custom macros written in VBA for handling Excel files

## Technologies

- **WPF**: For the user interface
- **Python**: For external processing and automation
- **VBA**: For macro scripting

## Installation

1. Clone the repository.
2. Double-click ProtocoLab.exe.

## How It Works
The tool offers two key features:

1. It compares an existing .tar file, which contains the extracted MRI fields, against an Excel file that outlines the physicists' requirements.
2. It generates requirements tailored to a specific MRI software type.

### Comparing
The user inputs the .tar file and .xls file into the designated text boxes, along with the MRI software type for the run. By clicking "Add," the user can include this specific execution in the data grid, where various actions can be performed, such as comparing multiple rows, removing rows, and opening results or the latest log.
All outputs are created under "cli\Data" in a folder that corresponds the MRI software type.

### Making Requirements
The user inputs the .tar file of which he wants to make requirements from. Then, by clicking "Make Requirements" the user can select which protocols he would like to include in requirements xls. The output is created under folder "cli\Requirements".

