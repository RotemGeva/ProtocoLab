using System.Windows;
using System.Windows.Controls;

namespace ProtocoLab
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        ListBox lvEntries = new();

        public MainWindow()
        {
            InitializeComponent();
        }
    }
}

        /*private void AddPath_Click(object sender, RoutedEventArgs e)
        {
            string inputFilePath = TarEntry.Text;
            string[] paths = lvEntries.Items.Cast<string>().ToArray();
            int index = Array.IndexOf(paths, TarEntry.Text);
            if (!File.Exists(inputFilePath))
                MessageBox.Show("Path does not exist on the computer!");
            else if (index != -1)
                MessageBox.Show("Path already exists!");
            else
                lvEntries.Items.Add(inputFilePath);
        }

        private void DeleteAllPaths_Click(object sender, RoutedEventArgs e)
        {
            lvEntries.Items.Clear();
            TarEntry.Text = "";
            ReqEntry.Text = "";

        }

        private void DeleteSelectedPath_Click(object sender, RoutedEventArgs e)
        {
            object item = lvEntries.SelectedItem;
            lvEntries.Items.Remove(item);
        }

        private void AddFromFile_Click(object sender, RoutedEventArgs e)
        {
            // Configure open file dialog box
            string[] paths = lvEntries.Items.Cast<string>().ToArray();
            var dialog = new Microsoft.Win32.OpenFileDialog();
            dialog.FileName = "Tar File"; // Default file name
            dialog.DefaultExt = ".tar"; // Default file extension
            dialog.Filter = "Tar files (.tar)|*.tar"; // Filter files by extension

            // Show open file dialog box
            bool? result = dialog.ShowDialog();

            // Process open file dialog box results
            if (result == true)
            {
                // Add path to list
                string filePath = dialog.FileName;
                int index = Array.IndexOf(paths, filePath);
                if (index != -1)
                    MessageBox.Show("Path already exists!");
                else
                    TarEntry.Text = filePath;
            }
        }

        private void AddFromFileReq_Click(object sender, RoutedEventArgs e)
        {
            // Configure open file dialog box
            var dialog = new Microsoft.Win32.OpenFileDialog();
            dialog.FileName = "Requiremenents File"; // Default file name
            dialog.DefaultExt = ".xlsx"; // Default file extension
            dialog.Filter = "Excel files (.xlsx)|*.xlsx"; // Filter files by extension

            // Show open file dialog box
            bool? result = dialog.ShowDialog();

            // Process open file dialog box results
            if (result == true)
            {
                string filePath = dialog.FileName;
                ReqEntry.Text = filePath;
            }
        }

        private void OpenRes_Click(object sender, RoutedEventArgs e)
        {
            const string fileEnding = "_Comparison";
            const string fileType = ".xlsx";
            string filePath = (string)lvEntries.SelectedItem;
            string directoryPath = System.IO.Path.GetDirectoryName((string)filePath);
            string lastFolderName = System.IO.Path.GetFileName(directoryPath);
            string newFileName = lastFolderName + fileEnding + fileType;
            Process.Start(System.IO.Path.Combine(directoryPath, newFileName));
        }

        private void Compare_Click(object sender, RoutedEventArgs e)
        {
            string tarFilePath = (string)lvEntries.SelectedItem;
            string reqFilePath = ReqEntry.Text;
            string folderName = MrName.Text;
            const string mainFolderName = "Compare\\Data";
            string scriptDirectory = System.IO.Path.GetDirectoryName(Environment.CurrentDirectory);
            scriptDirectory = System.IO.Path.Combine(scriptDirectory, mainFolderName);
            string newReqFile = folderName + "_Requirements.xlsx";
            if (!string.IsNullOrEmpty(folderName)) // Folder name is not empty
            {
                string folderPath = System.IO.Path.Combine(scriptDirectory, folderName);
                if (Directory.Exists(folderPath)) // Folder already exists
                {
                    MessageBoxResult result = MessageBox.Show("Folder already exists, all files will be removed. Do you want to continue?", "Warning", MessageBoxButton.YesNo);
                    if (result == MessageBoxResult.Yes)
                    {
                        DeleteAllFilesFromFolder(folderPath);
                    }
                }
                else
                    Directory.CreateDirectory(folderPath);
                File.Copy(reqFilePath, System.IO.Path.Combine(folderPath, newReqFile), true);
                reqFilePath = System.IO.Path.Combine(folderPath, newReqFile);
                HandleCompare(tarFilePath, reqFilePath);
                MessageBox.Show("Compare is done!");
            }
        }

        private void DeleteAllFilesFromFolder(string folderPath)
        {
            System.IO.DirectoryInfo di = new DirectoryInfo(folderPath);
            foreach (FileInfo file in di.GetFiles())
                file.Delete();
            foreach (DirectoryInfo dir in di.GetDirectories())
                dir.Delete(true);
        }

        private void KillExcelProcess()
        {
            Process[] excelProcesses = Process.GetProcessesByName("EXCEL");
            if (excelProcesses.Length > 0)
                foreach (Process process in excelProcesses)
                    process.Kill();
        }
        private void HandleCompare(string tarFilePath, string reqFilePath)
        {
            const string compareExe = "Compare.exe";
            KillExcelProcess();
            if (!string.IsNullOrEmpty(reqFilePath))
            {
                Process process = new Process();
                process.StartInfo.FileName = compareExe;
                process.StartInfo.Arguments = string.Format("-r {0} -t {1}", reqFilePath, tarFilePath);  // Format arguments
                process.Start();
                process.WaitForExit();
                MessageBox.Show("Compare is done!");
            }
            else
                MessageBox.Show("Requirements path is empty!");
        }

        private void CompareAll_Click(object sender, RoutedEventArgs e)
        {
            string reqFilePath = ReqEntry.Text;
            string[] paths = lvEntries.Items.Cast<string>().ToArray();
            for (int i = 0; i < paths.Length; i++)
                HandleCompare(reqFilePath, paths[i]);
            MessageBox.Show("Compare is done!");
        }*/

