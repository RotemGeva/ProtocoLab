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


namespace ProtocolsToolApp;

class MainWindowViewModel : BindableBase
{
    private static readonly ILogger _logger = Log.ForContext<MainWindowViewModel>();

    protected readonly IDialogService _dialogService;

    private readonly CompareCliApi.CliMgr _cliMgr;
    private readonly ObservableCollection<CompareItem> _compareItems = new();

    private CompareItem? _draftItem;
    private CompareItem? _selectedItem;
    
    private bool _isComparing;
    private bool _hasItems;

    public ReadOnlyObservableCollection<CompareItem> CompareItems { get; }

    /// <summary>
    /// Updates the <see cref="SelectedItem"/> from <see cref="DraftItem"/>
    /// </summary>
    public DelegateCommand UpdateSelectedItemCommand { get; }

    /// <summary>
    /// Adds the <see cref="DraftItem"/> to <see cref="CompareItems"/>
    /// </summary>
    public DelegateCommand AddItemCommand { get; }

    public DelegateCommand OpenResultCommand { get; }

    public DelegateCommand OpenFolderCommand { get; }

    public AsyncDelegateCommand CompareAsyncCommand { get; }
    public AsyncDelegateCommand CompareAllAsyncCommand { get; }

    public DelegateCommand DeleteItemCommand { get; }

    public DelegateCommand DeleteAllItemsCommand { get; }

    public DelegateCommand OpenFileFromDialogReqCommand { get; }

    public DelegateCommand OpenFileToCompareFromDialogCommand { get; }

    public DelegateCommand OpenProtocolExtractorCommand { get; }

    public DelegateCommand UploadInputFileCommand { get; }


    public MainWindowViewModel(IDialogService dialogService, CompareCliApi.CliMgr cliMgr)
    {
        _dialogService = dialogService;
        _cliMgr = cliMgr;
        CompareItems = new(_compareItems);

        DraftItem = new();

        _compareItems.CollectionChanged += (_, __) => HasItems = _compareItems.Any();

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
            .ObservesProperty(() => SelectedItem).ObservesProperty(() => IsComparing);

        CompareAllAsyncCommand = new AsyncDelegateCommand(CompareAllAsync, CanCompareAllAsync).ObservesProperty(() => HasItems).ObservesProperty(() => IsComparing);


        OpenFileFromDialogReqCommand = new DelegateCommand(OpenFileFromDialogReq, CanOpenFileFromDialogReq);

        OpenFileToCompareFromDialogCommand = new DelegateCommand(OpenFileToCompareFromDialog, CanOpenFileToCompareFromDialog);

        OpenProtocolExtractorCommand = new DelegateCommand(OpenProtocolExtractor, CanOpenProtocolExtractor);
        
        UploadInputFileCommand = new DelegateCommand(UploadInputFile, CanUploadInputFile);

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

    public bool HasItems
    {
        get => _hasItems;
        set => SetProperty(ref _hasItems, value);
    }

    public bool IsComparing
    {
        get => _isComparing;
        set => SetProperty(ref _isComparing, value);
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


    private bool CanCompareAllAsync() =>
        HasItems && !IsComparing;


    private async Task CompareAllAsync()
    {
        Process[] pname = Process.GetProcessesByName("EXCEL");
        if (pname.Length != 0)//excel is open
        {
            IDialogResult dr = await _dialogService.ShowDialogAsync("YesNoDialog", new DialogParameters("message=All excel processes will be terminated. " +
            "Did you save all your work?"));

            if (dr != null && dr.Result == ButtonResult.OK)
            {
                await HandleCompareAllAsync();
            }
        }
        else
            await HandleCompareAllAsync();
    }

    private async Task HandleCompareAllAsync()
    {
        IsComparing = true;
        bool isSuccess = true;
        _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Start comparing"));
        foreach (CompareItem item in _compareItems)
        {
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
                    item.ExecutionStatus = "Succeeded";
            }
            catch (Exception ex)
            {
                _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Compare tool failed to execute!"));
                item.ExecutionStatus = "Failed";
                _logger.Error(ex, "Compare tool failed to execute");
            }
        }
        if (isSuccess)
            _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=All terminated successfully!"));
        else
            _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Comparison process terminated with errors. Check log"));
        IsComparing = false;
    }


    private bool CanOpenResult() =>
        CompareRequest != null && File.Exists(_cliMgr.GetResultsPath(CompareRequest)) && !IsComparing;
    

    private void OpenResult()
    {
        if (!CanOpenResult()) return;

        Process process = new();
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

        _compareItems.Remove(SelectedItem!);
    }

    private bool CanDeleteAllItems() =>
        HasItems && !IsComparing;

    private void DeleteAllItems()
    {
        if (!CanDeleteAllItems()) return;

        _dialogService.ShowDialog("YesNoDialog", new DialogParameters("message=Are you sure you want to delete everything?"), dr =>
        {
;           if (dr != null && dr.Result == ButtonResult.OK)
                _compareItems.Clear();
        });
    }

    private bool CanCompareAsync() =>
        SelectedItem != null && !IsComparing;

    private async Task CompareAsync()
    {
        Process[] pname = Process.GetProcessesByName("EXCEL");
        if (pname.Length != 0)//excel is open
        {
            IDialogResult dr = await _dialogService.ShowDialogAsync("YesNoDialog", new DialogParameters("message=All excel processes will be terminated. " +
            "Did you save all your work?"));

            if (dr != null && dr.Result == ButtonResult.OK)
                await HandleCompareAsync();
        }
        else
            await HandleCompareAsync();
    }
    private async Task HandleCompareAsync()
    {
        CompareRequest request = CompareRequest!;
        IsComparing = true;
        try
        {
            _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Start comparing"));
            SelectedItem!.ExecutionStatus = "Running...";
            var exitCode = await _cliMgr.CompareAsync(request);
            if (exitCode != 0)
            {
                _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Compare failed"));
                SelectedItem!.ExecutionStatus = "Failed";
            }
            else
            {
                _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Compare succeded!"));
                SelectedItem!.ExecutionStatus = "Succeeded";
            }
        }
        catch (Exception ex)
        {
            _logger.Error(ex, "Compare tool failed to execute!");
            _dialogService.ShowDialog("NotificationDialog", new DialogParameters("message=Compare tool failed to execute!"));
            SelectedItem!.ExecutionStatus = "Failed";
        }
        finally
        {
            IsComparing = false;
        }
    }

    private bool CanOpenFileFromDialogReq() => true;

    private void OpenFileFromDialogReq()
    {
        if (!CanOpenFileFromDialogReq()) return;

        var dialog = new Microsoft.Win32.OpenFileDialog
        {
            FileName = "Excel File",
            DefaultExt = ".xlsx",
            Filter = "Excel files (.xlsx)|*.xlsx|All files (*.*)|*.*"
        };
        bool? result = dialog.ShowDialog();
        if (result == true)
            DraftItem!.ReqPath = dialog.FileName;
    }

    private bool CanOpenFileToCompareFromDialog() => true;

    private void OpenFileToCompareFromDialog()
    {
        if (!CanOpenFileToCompareFromDialog()) return;

        var dialog = new Microsoft.Win32.OpenFileDialog
        {
            FileName = "File to Compare",
            DefaultExt = ".tar",
            Filter = "(.tar)|*.tar|(.xml)|*.xml|All files (*.*)|*.*"
        };
        bool? result = dialog.ShowDialog();
        if (result == true)
            DraftItem!.ActualPath = dialog.FileName;
    }

    private bool CanOpenProtocolExtractor() => true;

    private void OpenProtocolExtractor()
    {
        string exePath = Path.Combine(Path.GetDirectoryName(System.Reflection.Assembly.GetEntryAssembly()!.Location)!, "cli", "Data", "ProtocolExtractor", "ProtocolExtractor.exe");
        Process process = new();
        process.StartInfo.FileName = exePath;
        process.StartInfo.WorkingDirectory = Path.GetDirectoryName(process.StartInfo.FileName);
        process.StartInfo.UseShellExecute = true;
        process.StartInfo.CreateNoWindow = false;
        process.Start();
    }

    private bool CanUploadInputFile() => true;

   
    /// <summary>
    /// <param name="latestLog">The most updated log in app's directory</param>
    /// <param name="records">Contains a list of all values of input file</param>
    /// <param name="appDirectory">The directory of ProtocolsApp, where logs are created</param>
    /// </summary>
    private void UploadInputFile()
    {
        var appDirectory = new DirectoryInfo(Path.Combine(Path.GetDirectoryName(System.Reflection.Assembly.GetEntryAssembly()!.Location)!));
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
            try
            {
                using (Stream stream = new FileStream(dialog.FileName, FileMode.Open)) // try to open input file.
                {
                    stream.Dispose(); // succeded to open input file = input file is closed; closing input file.
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

    // Checks if CSV input file contains valid values. If not, writes to log the invalid value and line number.
    private bool IsInputFileValid(List<InputFile> records)
    {
        bool isValid = true;
        foreach ((InputFile record, int index) in records.Select((record, index) => (record, index)))
        {
            if (!Path.Exists(record.ReqPath) || !Path.GetExtension(record.ReqPath).Equals(".xlsx"))
            {
                isValid = false;
                _logger.Error("Requirements file path: {ReqPath} is invalid [line: {Index}].", record.ReqPath, index + 1);
            }
            if (!Path.Exists(record.ActualPath) || Path.GetExtension(record.ActualPath) != ".tar")
            {
                isValid = false;
                _logger.Error("Actual file path: {ActualPath} is invalid [line: {Index}].", record.ActualPath, index + 1);
            }
        }
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
