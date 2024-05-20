using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.Diagnostics;
using System.IO;

namespace WPFUI
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
        }

        private void AddPath_Click(object sender, RoutedEventArgs e)
        {
            string[] paths = lvEntries.Items.Cast<string>().ToArray();
            int index = Array.IndexOf(paths, TarEntry.Text);
            if (index != -1)
                MessageBox.Show("Path already exists!");
            else
                lvEntries.Items.Add(TarEntry.Text);
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

        private void EditPath_Click(object sender, RoutedEventArgs e)
        {
            /* // Get the ListView item being edited
             var listViewItem = sender as FrameworkElement;
             if (listViewItem == null) return;

             // Get the edited data from the TextBox within the template
             var textBox = listViewItem.FindVisualChild<TextBox>();
             if (textBox == null) return;

             var editedPath = textBox.Text;

             // Update the data source with the edited path (replace with your logic)
             // YourPathList[selected item index].Path = editedPath;

             // Exit edit mode (assuming you're using some flag)
             listViewItem.IsEditing = false; */
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
                /*string filePath = dialog.FileName;
                int index = Array.IndexOf(paths, filePath);
                if (index != -1)
                    MessageBox.Show("Path already exists!");
                else
                    lvEntries.Items.Add(filePath);*/
            }
        }

        private void AddFromFileReq_Click(object sender, RoutedEventArgs e)
        {
            // Configure open file dialog box
            var dialog = new Microsoft.Win32.OpenFileDialog();
            dialog.FileName = "Tar File"; // Default file name
            dialog.DefaultExt = ".tar"; // Default file extension
            dialog.Filter = "Tar files (.tar)|*.tar"; // Filter files by extension

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
            string scriptDirectory = System.IO.Path.GetDirectoryName(Environment.CurrentDirectory);
            string newReqFile = folderName + "_Requirements";
            if (!string.IsNullOrEmpty(folderName)) // Folder name is not empty
            {
                string folderPath = System.IO.Path.Combine(scriptDirectory, "Data", folderName);
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
            KillExcelProcess();
            if (!string.IsNullOrEmpty(reqFilePath))
            {
                /*Process process = new Process();
                process.StartInfo.FileName = filePath;
                process.StartInfo.Arguments = string.Format("-r {0} -t {1}", reqFilePath, tarFilePath);  // Format arguments
                process.Start();*/
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
        }
    }
}

