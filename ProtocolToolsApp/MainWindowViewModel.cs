using CompareCli;
using Serilog;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using static CompareCli.CompareCliApi;
using System.Globalization;
using CsvHelper;
using CsvHelper.Configuration;
using CsvHelper.Configuration.Attributes;
using System.Reflection;
using System.Collections.Specialized;
using ICSharpCode.SharpZipLib.Tar;
using System.Text.RegularExpressions;
using Path = System.IO.Path;
using DryIoc;

namespace ProtocoLab;

class MainWindowViewModel : BindableBase
{
    private static readonly ILogger _logger = Log.ForContext<MainWindowViewModel>();

    protected readonly IDialogService _dialogService;

    private readonly CompareCliApi.CliMgr _cliMgr;
    private readonly ObservableCollection<CompareItem> _compareItems = new();

    private CompareItem? _draftItem;
    private CompareItem? _selectedItem;

    private bool _isComparing;
    private bool _isMakingRequirements;
    private bool _hasItems;
    private bool _hasSelectedItems;
    private bool _reqFolderExist;
    private bool _isComparisonInterrupted;
    private bool _isModifyComparisonSummaryChecked;

    public ReadOnlyObservableCollection<CompareItem> CompareItems { get; }

    /// <summary>
    /// Updates the <see cref="SelectedItem"/> from <see cref="DraftItem"/>
    /// </summary>
    public DelegateCommand UpdateSelectedItemCommand { get; }

    /// <summary>
    /// Adds the <see cref="DraftItem"/> to <see cref="CompareItems"/>
    /// </summary>
    public DelegateCommand AddItemCommand { get; }

    /// <summary>
    /// Open Excel comparison results.
    /// </summary>
    public DelegateCommand OpenResultCommand { get; }

    /// <summary>
    /// Open folder that contains all of the comparison results.
    /// </summary>
    public DelegateCommand OpenFolderCommand { get; }

    public DelegateCommand DeleteItemCommand { get; }

    public DelegateCommand DeleteAllItemsCommand { get; }

    public DelegateCommand OpenFileFromDialogReqCommand { get; }

    public DelegateCommand OpenFileToCompareFromDialogCommand { get; }

    public DelegateCommand UploadInputFileCommand { get; }

    public DelegateCommand OpenLatestLogCommand { get; }
    public DelegateCommand OpenLogCommand { get; }
    public DelegateCommand InterruptComparisonCommand { get; }



    /// <summary>
    /// Open the folder the conatins all the created requirements.
    /// </summary>
    public DelegateCommand OpenRequirementsCommand { get; }
    public DelegateCommand SelectAllCommand { get; }
    public DelegateCommand UnselectAllCommand { get; }

    public AsyncDelegateCommand CompareAsyncCommand { get; }
    public AsyncDelegateCommand CompareAllAsyncCommand { get; }
    public AsyncDelegateCommand MakeRequirementsAsyncCommand { get; }


    public MainWindowViewModel(IDialogService dialogService, CompareCliApi.CliMgr cliMgr)
    {
        _dialogService = dialogService;
        _cliMgr = cliMgr;
        CompareItems = new(_compareItems);

        DraftItem = new();

        _compareItems.CollectionChanged += (_, e) =>
        {
            HasItems = _compareItems.Any();
            compareItemsChanged(_, e);
        };

        UpdateSelectedItemCommand = new DelegateCommand(UpdateSelectedItem, CanUpdateSelectedItem)
            .ObservesProperty(() => SelectedItem)
            .ObservesProperty(() => DraftItem);

        AddItemCommand = new DelegateCommand(AddItem, CanAddItem);

        OpenResultCommand = new DelegateCommand(OpenResult, CanOpenResult)
            .ObservesProperty(() => SelectedItem).ObservesProperty(() => IsComparing);

        OpenFolderCommand = new DelegateCommand(OpenFolder, CanOpenFolder)
            .ObservesProperty(() => SelectedItem).ObservesProperty(() => IsComparing);

        DeleteItemCommand = new DelegateCommand(DeleteItem, CanDeleteItem)
            .ObservesProperty(() => SelectedItem).ObservesProperty(() => IsComparing);

        DeleteAllItemsCommand = new DelegateCommand(DeleteAllItems, CanDeleteAllItems).ObservesProperty(() => HasItems).ObservesProperty(() => IsComparing);

        CompareAsyncCommand = new AsyncDelegateCommand(CompareAsync, CanCompareAsync)
            //.ObservesProperty(() => SelectedItem)
            .ObservesProperty(() => HasSelectedItems)
            .ObservesProperty(() => IsComparing);

        CompareAllAsyncCommand = new AsyncDelegateCommand(CompareAllAsync, CanCompareAllAsync).ObservesProperty(() => HasItems).ObservesProperty(() => IsComparing);
        MakeRequirementsAsyncCommand = new AsyncDelegateCommand(MakeRequirementsAsync, CanMakeRequirementsAsync).ObservesProperty(() => DraftItem.ActualPath)
        .ObservesProperty(() => IsMakingRequirements);

        OpenFileFromDialogReqCommand = new DelegateCommand(OpenFileFromDialogReq, CanOpenFileFromDialogReq);
        OpenFileToCompareFromDialogCommand = new DelegateCommand(OpenFileToCompareFromDialog, CanOpenFileToCompareFromDialog);

        UploadInputFileCommand = new DelegateCommand(UploadInputFile, CanUploadInputFile);

        OpenLatestLogCommand = new DelegateCommand(OpenLatestLog, CanOpenLatestLog);
        OpenLogCommand = new DelegateCommand(OpenLog, CanOpenLog).ObservesProperty(() => SelectedItem);

        OpenRequirementsCommand = new DelegateCommand(OpenRequirements, CanOpenRequirements);

        SelectAllCommand = new DelegateCommand(SelectAll, CanSelectAll).ObservesProperty(() => HasItems).ObservesProperty(() => IsComparing);
        UnselectAllCommand = new DelegateCommand(UnselectAll, CanUnselectAll).ObservesProperty(() => HasSelectedItems).ObservesProperty(() => IsComparing);

        InterruptComparisonCommand = new DelegateCommand(InterruptComparison, CanInterruptComparison).ObservesProperty(() => IsComparing);

        void compareItemsChanged(object? sender, NotifyCollectionChangedEventArgs e)
        {
            switch (e.Action)
            {
                // NewItems: represents the items that were added to or replaced in the collection 
                case NotifyCollectionChangedAction.Add:
                    foreach (CompareItem item in e.NewItems!)
                        item.PropertyChanged += onItemPropertyChanged;
                    break;
                case NotifyCollectionChangedAction.Remove:
                    HasSelectedItems = _compareItems.Any(x => x.IsSelected);
                    foreach (CompareItem item in e.OldItems!)
                        item.PropertyChanged -= onItemPropertyChanged;
                    break;
                case NotifyCollectionChangedAction.Replace:
                    break;
                case NotifyCollectionChangedAction.Move:
                    break;
                case NotifyCollectionChangedAction.Reset:
                    break;
                default:
                    break;
            }

        }

        void onItemPropertyChanged(object? sender, PropertyChangedEventArgs e)
        {
            switch (e.PropertyName)
            {
                case nameof(CompareItem.IsSelected):
                    HasSelectedItems = _compareItems.Any(x => x.IsSelected);
                    break;
            }
        }

    }

    public CompareItem? DraftItem
    {
        get => _draftItem;

        set
        {
            //Create event handler that will be called.
            void onDraftItemPropertyChanged(object? _, PropertyChangedEventArgs __)
            {
                UpdateSelectedItemCommand.RaiseCanExecuteChanged();
                AddItemCommand.RaiseCanExecuteChanged();
            }

            if (value != _draftItem) //Checks if a new DraftItem object was created (=a row was selected).
            {
                if (_draftItem != null)
                    _draftItem.PropertyChanged -= onDraftItemPropertyChanged;
                //If textboxes are full, activate event handler so it checks if an update or an adding is needed.
                if (value != null)
                    value.PropertyChanged += onDraftItemPropertyChanged;

                _draftItem = value;

                RaisePropertyChanged();
            }
        }
    }

    public CompareItem? SelectedItem
    {
        get => _selectedItem;
        set => SetProperty(ref _selectedItem, value, () =>
        {
            //If a row was selected, put row's data into a new DraftItem => activate set of DraftItem.
            DraftItem = value == null ? new() : new(value);
        });
    }

    public bool IsModifyComparisonSummaryChecked
    {
        get => _isModifyComparisonSummaryChecked;
        set => SetProperty(ref _isModifyComparisonSummaryChecked, value);
    }

    public bool HasItems
    {
        get => _hasItems;
        set => SetProperty(ref _hasItems, value);
    }

    public bool HasSelectedItems
    {
        get => _hasSelectedItems;
        set => SetProperty(ref _hasSelectedItems, value);
    }

    public bool IsComparing
    {
        get => _isComparing;
        set => SetProperty(ref _isComparing, value);
    }
    public bool IsMakingRequirements
    {
        get => _isMakingRequirements;
        set => SetProperty(ref _isMakingRequirements, value);
    }

    public bool IsComparisonInterrupted
    {
        get => _isComparisonInterrupted;
        set => SetProperty(ref _isComparisonInterrupted, value);
    }


    private CompareRequest? CompareRequest => SelectedItem == null ?
        null : new(SelectedItem.MrType!, SelectedItem.ReqPath!, SelectedItem.ActualPath!);

    private bool CanUpdateSelectedItem() =>
        DraftItem != null && SelectedItem != null && !DraftItem.Equals(SelectedItem) && DraftItem.IsValid;

    private void UpdateSelectedItem()
    {
        if (!CanUpdateSelectedItem())
            return;

        SelectedItem!.Copy(DraftItem!);
        SelectedItem.ExecutionStatus = "";

        OpenResultCommand?.RaiseCanExecuteChanged();
        OpenFolderCommand?.RaiseCanExecuteChanged();
    }



    private bool CanAddItem() =>
        DraftItem != null && DraftItem.IsValid && !_compareItems.Any(ci => ci.Identical(DraftItem));

    private void AddItem()
    {
        if (!CanAddItem())
            return;

        if (Directory.Exists(Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "cli", "Data", DraftItem!.MrType!)))
        {
            _dialogService.ShowDialog("YesNoDialog", new DialogParameters("message=The folder name already exists. " +
            "If you proceed, the older comparison results in the folder will be retained. Would you like to continue?"), callback: (dr) =>
            {
                if (dr != null && dr.Result == ButtonResult.OK)
                    _compareItems.Add(new(DraftItem!));
            });
        }
        else
            _compareItems.Add(new(DraftItem!));
    }

    private bool CanCompareAsync() =>
        HasSelectedItems && !IsComparing;

    private async Task CompareAsync()
    {
        Process[] pname = Process.GetProcessesByName("EXCEL");
        if (pname.Length != 0)//excel is open
        {
            _logger.Information("Excel proccess is running in background. Presenting YesNoDialog...");
            IDialogResult dr = await _dialogService.ShowDialogAsync("YesNoDialog", new DialogParameters("message=All excel processes will be terminated. " +
            "Did you save all your work?"));

            if (dr != null && dr.Result == ButtonResult.OK)
            {
                _logger.Information("User approved to force close Excel.");
                await HandleCompareAsync();
            }
            else
                _logger.Information("User aborted force close Excel dialog.");
        }
        else
        {
            _logger.Information("Excel process is not running in the background.");
            await HandleCompareAsync();
        }
    }
    private async Task HandleCompareAsync()
    {
        await HandleCompareAllAsync(selectedOnly: true);
    }
    private bool CanCompareAllAsync() =>
        HasItems && !IsComparing;


    private async Task CompareAllAsync()
    {
        _logger.Information("Compare All clicked...");
        Process[] pname = Process.GetProcessesByName("EXCEL");
        if (pname.Length != 0)//excel is open
        {
            _logger.Information("Excel proccess is running in background. Presenting YesNoDialog...");
            IDialogResult dr = await _dialogService.ShowDialogAsync("YesNoDialog", new DialogParameters("message=All excel processes will be terminated. " +
            "Did you save all your work?"));

            if (dr != null && dr.Result == ButtonResult.OK)
            {
                _logger.Information("User approved to force close Excel.");
                await HandleCompareAllAsync();
            }
            else
                _logger.Information("User aborted force close Excel dialog.");
        }
        else
        {
            _logger.Information("Excel process is not running in the background.");
            await HandleCompareAllAsync();
        }
    }

    private async Task HandleCompareAllAsync(bool selectedOnly = false)
    {
        // Handling comparison summary files
        _logger.Information($"ModifyComparisonSummary status is: {IsModifyComparisonSummaryChecked}");
        if (IsModifyComparisonSummaryChecked == true)
        {
            FileInfo comparisonSummaryFilepath = new(Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "cli", "Data", "Comparison_Summary.csv"));
            FileInfo comparisonDetailesSummaryFilepath = new(Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "cli", "Data", "Comparison_Details_Summary.txt"));
            AddTimestamp(comparisonSummaryFilepath);
            AddTimestamp(comparisonDetailesSummaryFilepath);
        }

        
        // Handling compare process
        _logger.Information($"Starting to compare all with selectedOnly mode: {selectedOnly}");
        IsComparing = true;
        _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Start comparing..."));
        var itemsToCompare = selectedOnly ? _compareItems.Where(x => x.IsSelected) : _compareItems;

        // Restarting execution status
        foreach (CompareItem item in itemsToCompare) 
        {
            _logger.Information($"Restarting execution status for: {item.MrType}.");
            item.ExecutionStatus = "";
        }

        bool isSuccess = true;
        foreach (CompareItem item in itemsToCompare)
        {
            if (!IsComparisonInterrupted) {
                CompareRequest request = new(item.MrType!, item.ReqPath!, item.ActualPath!);
                try
                {
                    item.ExecutionStatus = "Running...";
                    var exitCode = await _cliMgr.CompareAsync(request);
                    if (exitCode != 0)
                    {
                        isSuccess = false;
                        item.ExecutionStatus = "Failed";
                        _logger.Error("Compare with parameters: {@Request} failed", request);
                    }
                    else
                    {
                        item.ExecutionStatus = "Succeeded";
                        _logger.Information("Compare with parameters: {@Request} succeded", request);
                    }
                }
                catch (Exception ex)
                {
                    _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Compare tool failed to execute!"));
                    item.ExecutionStatus = "Failed";
                    _logger.Error(ex, "Compare tool failed to execute");
                }
            }

            else
            {
                _logger.Information("The comparison process was interrupted.");
                IsComparing = false;
                return;
            }
        }
        if (isSuccess)
            _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=All terminated successfully!"));
        else
            _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=The comparison process terminated with errors. Check log"));
        IsComparing = false;
        IsModifyComparisonSummaryChecked = false;
        OpenLatestLogCommand.RaiseCanExecuteChanged();

        void AddTimestamp(FileInfo file)
        {
            DateTime timestamp = DateTime.Now;
            string formattedTimestamp = timestamp.ToString("ddMMyy_HHmmss");

            if (file.Exists)
            {
                _logger.Information($"{file.FullName} exists. Adding timstamp to file...");
                string newFileName = file.Name.Replace(file.Name, Path.GetFileNameWithoutExtension(file.Name) + "_" + formattedTimestamp + file.Extension);
                string newFilePath = Path.Combine(file.DirectoryName!, newFileName);
                File.Move(file.FullName, newFilePath);
            }
            else _logger.Information($"{file.FullName} does not exist.");
        }
    }

    private bool CanInterruptComparison() => IsComparing;

    private void InterruptComparison()
    {
        if (!CanInterruptComparison()) return;
        IsComparisonInterrupted = true;
        _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=The comparison process was interrupted and " +
            "will end after the current run."));
    }


    private bool CanOpenResult() =>
        CompareRequest != null && File.Exists(_cliMgr.GetResultsPath(CompareRequest)) && !IsComparing;


    private void OpenResult()
    {
        if (!CanOpenResult()) return;       
        Process process = new();
        _logger.Information($"Opening results of: {Path.GetDirectoryName(process.StartInfo.FileName)}...");
        process.StartInfo.FileName = _cliMgr.GetResultsPath(CompareRequest!);
        process.StartInfo.WorkingDirectory = Path.GetDirectoryName(process.StartInfo.FileName);
        process.StartInfo.UseShellExecute = true;
        process.StartInfo.CreateNoWindow = true;
        process.Start();
    }

    private bool CanOpenFolder() =>
        CompareRequest != null && Directory.Exists(_cliMgr.GetFolderPath(CompareRequest)) && !IsComparing;


    private void OpenFolder()
    {
        if (!CanOpenFolder()) return;

        _logger.Information($"Opening results folder: {_cliMgr.GetFolderPath(CompareRequest!)}...");
        var psi = new ProcessStartInfo()
        {
            FileName = _cliMgr.GetFolderPath(CompareRequest!),
            UseShellExecute = true
        };
        Process.Start(psi);
    }

    private bool CanDeleteItem() =>
        SelectedItem != null && !IsComparing;

    private void DeleteItem()
    {
        if (!CanDeleteItem()) return;

        _logger.Information($"Removing {SelectedItem} from data grid...");
        _compareItems.Remove(SelectedItem!);
    }

    private bool CanDeleteAllItems() =>
        HasItems && !IsComparing;

    private void DeleteAllItems()
    {
        if (!CanDeleteAllItems()) return;

        _logger.Information("User requested to delete all items in data grid. Presenting YesNoDialog...");
        _dialogService.ShowDialog("YesNoDialog", new DialogParameters("message=Are you sure you want to delete everything?"), dr =>
        {
            ; if (dr != null && dr.Result == ButtonResult.OK)
            {
                _logger.Information("User clicked yes to delete all items in data grid. Clearing data grid...");
                _compareItems.Clear();
            }
        });
    }



    private bool CanOpenFileFromDialogReq() => true;

    private void OpenFileFromDialogReq()
    {
        if (!CanOpenFileFromDialogReq()) return;

        var dialog = new Microsoft.Win32.OpenFileDialog
        {
            FileName = "Excel File",
            DefaultExt = ".xlsx",
            Filter = "Excel files (.xlsx)|*.xlsx|All files (*.*)|*.*",
            InitialDirectory = Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "cli", "Data")
        };
        bool? result = dialog.ShowDialog();
        if (result == true)
        {
            _logger.Information($"User loaded {dialog.FileName}.");
            DraftItem!.ReqPath = dialog.FileName;
        }
    }

    private bool CanOpenFileToCompareFromDialog() => true;

    private void OpenFileToCompareFromDialog()
    {
        if (!CanOpenFileToCompareFromDialog()) return;

        var dialog = new Microsoft.Win32.OpenFileDialog
        {
            FileName = "File to Compare",
            DefaultExt = ".tar",
            Filter = "Tar or XML files (*.tar;*.xml)|*.tar;*.xml|All files (*.*)|*.*"
        };
        bool? result = dialog.ShowDialog();
        if (result == true)
        {
            _logger.Information($"User loaded {dialog.FileName}.");
            DraftItem!.ActualPath = dialog.FileName;
        }
    }



    private bool CanUploadInputFile() => true;


    /// <summary>
    /// <param name="latestLog">The most updated log in app's directory</param>
    /// <param name="records">Contains a list of all values of input file</param>
    /// <param name="appDirectory">The directory of ProtocolsApp, where logs are created</param>
    /// </summary>
    private void UploadInputFile()
    {
        var appDirectory = new DirectoryInfo(Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "Logs"));
        var latestLog = (from f in appDirectory.GetFiles("*.log") orderby f.LastWriteTime descending select f).First(); // get most updated log
        var dialog = new Microsoft.Win32.OpenFileDialog
        {
            FileName = "CSV File",
            DefaultExt = ".csv",
            Filter = "CSV files (.csv)|*.csv|All files (*.*)|*.*"
        };
        bool? result = dialog.ShowDialog();
        if (result == true)
        {
            _logger.Information($"User uploaded external file. Reading file content...");
            try
            {
                using (Stream stream = new FileStream(dialog.FileName, FileMode.Open)) // try to open input file.
                {
                    stream.Dispose(); // succeded to open input file = input file is not in use; closing input file.
                    var config = CsvConfiguration.FromAttributes<InputFile>();
                    using StreamReader reader = new(dialog.FileName);
                    using var csv = new CsvReader(reader, config);
                    List<InputFile> records = csv.GetRecords<InputFile>().ToList();
                    bool isValid = IsInputFileValid(records);
                    if (isValid)
                    {
                        foreach (InputFile record in records)
                        {
                            CompareItem itemToAdd = new(record.MrType!, record.ReqPath!, record.ActualPath!);
                            if (!_compareItems.Contains(itemToAdd))
                                _compareItems.Add(itemToAdd);
                        }
                    }
                    else
                    {
                        _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Input file has invalid values. See log"));
                        Process.Start("notepad.exe", latestLog.FullName); // open log with notepad
                    }
                }
            } // file could not open or in is in use
            catch (Exception ex)
            {
                _logger.Error(ex, "Failed to load input file.");
                _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Input file is corrupted. See log"));
                Process.Start("notepad.exe", latestLog.FullName);
            }
        }
    }

    private bool CanMakeRequirementsAsync()
    {
        return DraftItem!.ActualPath != null && File.Exists(DraftItem.ActualPath) && !IsMakingRequirements;
    }

    private async Task MakeRequirementsAsync()
    {
        _logger.Information("User requested to make requirements.");
        Process[] pname = Process.GetProcessesByName("EXCEL");
        var fileExtension = Path.GetExtension(DraftItem!.ActualPath);

        var mode = fileExtension switch
        {
            ".tar" => "GE",
            ".xml" => "Siemens",
            _ => null 
        };

        if (pname.Length != 0)//excel is open
        {
            IDialogResult dr = await _dialogService.ShowDialogAsync("YesNoDialog", new DialogParameters("message=All excel processes will be terminated. " +
            "Did you save all your work?"));

            if (dr != null && dr.Result == ButtonResult.OK)
            {
                await HandleMakeRequirementsAsync(mode!);
                OpenRequirementsCommand.RaiseCanExecuteChanged();
            }
        }
        else
        {
            await HandleMakeRequirementsAsync(mode!);
            OpenRequirementsCommand.RaiseCanExecuteChanged();
        }
    }

    private async Task HandleMakeRequirementsAsync(string mode)
    {
        _logger.Information($"Start handling requirements with in mode: {mode}");
        IsMakingRequirements = true;

        var contentFolder = Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "cli", "Data", "temp");
        var existedProtocols = new List<string>();
        switch (mode)
        {
            case "GE":
                ExtractTar(DraftItem!.ActualPath!, contentFolder);
                existedProtocols = ExtractProtocolsNames(contentFolder);
                break;
            case "Siemens":
                var parsingExitCode = await HandleXMLParsing();
                if (parsingExitCode != 0)
                {
                    IsMakingRequirements = false;
                    return;
                }
                existedProtocols = ReadProtocolsNames(contentFolder);
                break;
        }

        var parameters = new DialogParameters
        {
            { "items", existedProtocols }
        };


        var result = await _dialogService.ShowDialogAsync(nameof(SelectionDialog), parameters);

        if (result.Result == ButtonResult.OK)
        {
            var selectedProtocols = result.Parameters.GetValue<List<string>>("selectedItems");
            var request = new MakeReqRequest(DraftItem!.ActualPath!, selectedProtocols);
            await _dialogService.ShowDialogAsync("NotificationDialog", new DialogParameters("message=Creating a requirements file from the selected protocols"));
            var exitCode = await _cliMgr.MakeReqAsync(request, selectedProtocols);
            if (exitCode != 0)
            {
                _logger.Error("Make requirements with parameters: {@Request} failed", request);
                await _dialogService.ShowDialogAsync("NotificationDialog", new DialogParameters("message=Making requirements failed"));
            }
            else
            {
                _logger.Information("Make requirements with parameters: {@Request} succeded", request);
                await _dialogService.ShowDialogAsync("NotificationDialog", new DialogParameters("message=Making requirements succeded!"));
            }
        }

        IsMakingRequirements = false;

        /// <summary>
        /// Reads protocols list, that is found in a txt file, out of a given folder.
        /// </summary>
        /// <param name="folderPath">The directory that contains that txt file.</param>
        List<string> ReadProtocolsNames(string folderPath)
        {
            _logger.Information($"Reading protocols names from: {folderPath}...");
            var txtFilepath = Directory.GetFiles(folderPath, "*.txt")[0];
            var protocolsList = File.ReadAllText(txtFilepath)
                   .Split(',')
                   .Select(item => item.Trim())
                   .ToList();
            _logger.Information($"The protocols in file are: {string.Join(", ", protocolsList)}...");
            return protocolsList;
        }
        /// <summary>
        /// Extracts the contents of a tar file to a specified directory.
        /// </summary>
        /// <param name="tarFilePath">The path to the tar file.</param>
        /// <param name="destinationFolder">The directory to extract the tar file into.</param>
        void ExtractTar(string tarFilePath, string destinationFolder)
        {
            _logger.Information($"Extracting protocols from tar: {destinationFolder}...");
            if (Directory.Exists(destinationFolder))
                Directory.Delete(destinationFolder, true);
            Directory.CreateDirectory(destinationFolder);

            try
            {
                using (var tarStream = new FileStream(tarFilePath, FileMode.Open, FileAccess.Read, FileShare.Read))
                using (var tarArchive = new TarInputStream(tarStream))
                {
                    TarEntry entry;
                    while ((entry = tarArchive.GetNextEntry()) != null)
                    {
                        // Combine the destination path with the entry name
                        var entryPath = Path.Combine(destinationFolder, entry.Name);

                        if (entry.IsDirectory)
                            // Ensure directory exists
                            Directory.CreateDirectory(entryPath);
                        else
                        {
                            // Ensure directory exists
                            var entryDirectory = Path.GetDirectoryName(entryPath);
                            if (!Directory.Exists(entryDirectory))
                                Directory.CreateDirectory(entryDirectory);

                            // Extract the file
                            using (var entryStream = File.Create(entryPath))
                            {
                                tarArchive.CopyEntryContents(entryStream);
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.Error(ex, "Failed to extract tar file.");
                _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Tar file could not be extracted. See log"));
            }
        }
        /// <summary>
        /// Extracts protocol name from a directory that contains tar content.
        /// </summary>
        /// <param name="directoryPath">The path of the directory that contains the protocols.</param>
        List<string> ExtractProtocolsNames(string directoryPath)
        {
            _logger.Information($"Extracting protocols names from {directoryPath}.");
            // Regex pattern to match folder names
            var pattern = @"^adult_other_(.+?)_\d+_\d+$";
            var regex = new Regex(pattern, RegexOptions.Compiled);

            // List to store matching folder names
            List<string> matchingFolders = new List<string>();

            // Get all folder names in the directory
            var folderNames = Directory.GetDirectories(directoryPath);

            foreach (var folderPath in folderNames)
            {
                var folderName = Path.GetFileName(folderPath);

                // Match the folder name with the regex pattern
                var match = regex.Match(folderName);

                if (match.Success)
                {
                    _logger.Information($"{folderPath} contained regex pattern.");
                    // Extract the captured group
                    var extractedName = match.Groups[1].Value;

                    // Add the matching name to the list
                    matchingFolders.Add(extractedName);
                }
            }
            _logger.Information($"The matching folders are: {matchingFolders.Aggregate((x, y) => $"{x} {y}")}.");
            return matchingFolders;
        }
    }

    private async Task<int> HandleXMLParsing()
    {
        var existedProtocols = new List<string>();
        var parseXMLrequest = new ParseXMLRequest(DraftItem!.ActualPath!);
        var parsingExitCode = await _cliMgr.ParseXMLAsync(parseXMLrequest, DraftItem!.ActualPath!);
        if (parsingExitCode != 0)
        {
            _logger.Error("Parsing XML with parameters: {@Request} failed", parseXMLrequest);
            await _dialogService.ShowDialogAsync("NotificationDialog", new DialogParameters("message=Parsing XML failed. The requirements process cannot continue"));
        }
        else
        {
            _logger.Information("Parsing XML with parameters: {@Request} succeded", parseXMLrequest);
            await _dialogService.ShowDialogAsync("NotificationDialog", new DialogParameters("message=Parsing XML succeded! Press OK to continue the requirements process"));
        }
        return parsingExitCode;
    }
    


    private bool CanOpenRequirements()
    {
        string requirementsFolderPath = Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "cli", "Data", "Requirements");
        if (Directory.Exists(requirementsFolderPath))
            return true;
        return false;
    }


    private void OpenRequirements()
    {
        if (!CanOpenRequirements()) return;

        string requirementsFolderPath = Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "cli", "Data", "Requirements");
        if (Directory.Exists(requirementsFolderPath))
        {
            var psi = new ProcessStartInfo()
            {
                FileName = requirementsFolderPath,
                UseShellExecute = true
            };
            Process.Start(psi);
        }
    }

    private bool CanSelectAll() => HasItems && !IsComparing;

    private void SelectAll()
    {
        if (!CanSelectAll()) return;

        foreach (var item in _compareItems)
            item.IsSelected = true; 
        HasSelectedItems = true;
    }

    private bool CanUnselectAll() => HasSelectedItems && !IsComparing;

    private void UnselectAll()
    {
        if (!CanUnselectAll()) return;

        foreach (var item in _compareItems)
            item.IsSelected = false;
        HasSelectedItems = false;
    }

    private bool CanOpenLog()
    {
        if (CompareRequest == null) return false;
        else
        {
            string logsFolder = Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "cli", "ExternalToolLogs");
            if (!Directory.Exists(logsFolder)) return false;
            string prefix = $"Compare-{CompareRequest.MrType}";
            string[] logs = Directory.GetFiles(logsFolder, prefix + "*");
            _logger.Information($"Found {logs.Length} matching logs that start with: {prefix}.");
            return !IsComparing && Directory.Exists(logsFolder) && logs.Length > 0;
        }
    } 

    
    private void OpenLog()
    {
        if (!CanOpenLog()) return;
        string logsFolder = Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "cli", "ExternalToolLogs");
        string prefix = $"Compare-{CompareRequest!.MrType}";
        string[] logs = Directory.GetFiles(logsFolder, prefix + "*");
        var sortedLogs = logs.OrderByDescending(file => File.GetCreationTime(file)).ToArray();
        _logger.Information($"The latest log that contains the prefix: {prefix} is: {sortedLogs[0]}.");
        Process.Start("notepad.exe", sortedLogs[0]);
    }


    private bool CanOpenLatestLog()
    {
        string logsFolderPath = Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "cli", "ExternalToolLogs");
        if (Directory.Exists(logsFolderPath))
        {
            if (!Directory.EnumerateFileSystemEntries(logsFolderPath).Any()) return false; // Checks if logs folder is empty. 
            else return true;
        }
        return false;
    }

    private void OpenLatestLog()
    {
        if (!CanOpenLatestLog()) return;
        var logsFolder = new DirectoryInfo(Path.Combine(Path.GetDirectoryName(Assembly.GetEntryAssembly()!.Location)!, "cli", "ExternalToolLogs"));
        var latestLog = (from f in logsFolder.GetFiles("*.log") orderby f.LastWriteTime descending select f).First();
        _logger.Information($"Latest log file that was found in folder: {logsFolder} is: {latestLog}. Opening file in notepad.exe...");
        Process.Start("notepad.exe", latestLog.FullName);
    }


    /// <summary>
    ///  Checks if CSV input file contains valid values. If not, writes to log the invalid value and line number.
    /// </summary>
    /// <param name="records">Lines of CSV file.</param>
    /// <returns></returns>
    private bool IsInputFileValid(List<InputFile> records)
    {
        _logger.Information("Verifying input file is valid...");
        bool isValid = true;
        foreach ((InputFile record, int index) in records.Select((record, index) => (record, index)))
        {
            if (!Path.Exists(record.ReqPath) || !Path.GetExtension(record.ReqPath).Equals(".xlsx"))
            {
                isValid = false;
                _logger.Error("Requirements file path: {ReqPath} is invalid [line: {Index}].", record.ReqPath, index + 1);
            }
            if (!Path.Exists(record.ActualPath) && (Path.GetExtension(record.ActualPath) != ".tar" || Path.GetExtension(record.ActualPath) != ".xml"))
            {
                isValid = false;
                _logger.Error("Actual file path: {ActualPath} is invalid [line: {Index}].", record.ActualPath, index + 1);
            }
        }
        _logger.Information($"Input file validation result: {isValid}.");
        return isValid;
    }

    [Delimiter(",")]
    [CultureInfo("en-US")]
    private class InputFile
    {
        public string? MrType { get; set; }
        public string? ReqPath { get; set; }
        public string? ActualPath { get; set; }
    }

}
