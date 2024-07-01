using CompareCli;
using DryIoc;
using Prism.Dialogs;
using Serilog;
using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.Eventing.Reader;
using System.Formats.Tar;
using System.IO;
using System.Windows;
using static CompareCli.CompareCliApi;

namespace ProtocolToolsApp;

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

    /// <summary>
    /// Opens comparison output file if exists.
    /// </summary>
    public DelegateCommand OpenResultCommand { get; }

    public DelegateCommand OpenFolderCommand { get; }

    public AsyncDelegateCommand CompareAsyncCommand { get; }
    public AsyncDelegateCommand CompareAllAsyncCommand { get; }

    public DelegateCommand DeleteItemCommand { get; }

    public DelegateCommand DeleteAllItemsCommand { get; }

    public DelegateCommand OpenFileFromDialogReqCommand { get; }

    public DelegateCommand OpenFileToCompareFromDialogCommand { get; }

    public DelegateCommand OpenProtocolExtractorCommand { get; }


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

    }

    private bool CanOpenProtocolExtractor()
    {
        return !Process.GetProcessesByName("ProtocolExtractor").Any();
    }

    private void OpenProtocolExtractor()
    {
        string exePath = Path.Combine(Path.GetDirectoryName(System.Reflection.Assembly.GetEntryAssembly()!.Location)!, "cli", "Data", "ProtocolExtractor", "ProtocolExtractor.exe");
        Process process = new Process();
        process.StartInfo.FileName = exePath;
        process.StartInfo.WorkingDirectory = Path.GetDirectoryName(process.StartInfo.FileName);
        process.StartInfo.UseShellExecute = true;
        process.StartInfo.CreateNoWindow = false;
        process.Start();
    }

    public CompareItem? DraftItem
    {
        get => _draftItem;

        set
        {
            void onDraftItemPropertyChanged(object? _, PropertyChangedEventArgs __)
            {
                UpdateSelectedItemCommand.RaiseCanExecuteChanged();
                AddItemCommand.RaiseCanExecuteChanged();
            }

            if (value != _draftItem)
            {
                if (_draftItem != null)
                    _draftItem.PropertyChanged -= onDraftItemPropertyChanged;
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

        OpenResultCommand?.RaiseCanExecuteChanged();
        OpenFolderCommand?.RaiseCanExecuteChanged();
    }



    private bool CanAddItem() =>
        DraftItem != null && DraftItem.IsValid && !_compareItems.Any(ci => ci.Identical(DraftItem));

    private void AddItem()
    {
        if (!CanAddItem())
            return;

        if (Directory.Exists(Path.Combine(Path.GetDirectoryName(System.Reflection.Assembly.GetEntryAssembly()!.Location)!, "cli", "Data", DraftItem!.MrType!)))
        {
            _dialogService.ShowDialog("YesNoDialog", new DialogParameters("message=The folder name already exists. " +
            "Adding will overwrite its current contents during the comparison process."), callback: (dr) =>
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
        IDialogResult dr = await _dialogService.ShowDialogAsync("YesNoDialog", new DialogParameters("message=All excel processes will be terminated. " +
            "Did you save all your work?"));

        if (dr != null && dr.Result == ButtonResult.OK)
        {
            IsComparing = true;
            _dialogService.ShowDialog("YesNoDialog", new DialogParameters("message=Start comparing"));
            foreach (CompareItem item in _compareItems)
            {
                CompareRequest request = new(item.MrType!, item.ReqPath!, item.ActualPath!);
                try
                {
                    var result = await _cliMgr.CompareAsync(request);
                    _logger.Error("Compare tool success");
                }
                catch (Exception ex)
                {
                    _dialogService.ShowDialog("YesNoDialog", new DialogParameters("message=Compare was failed!"));
                    _logger.Error(ex, "Compare tool failed");
                }
            }
            _dialogService.ShowDialog("YesNoDialog", new DialogParameters("message=Compare is done!"));
            IsComparing = false;
        }
    }


    private bool CanOpenResult() =>
        CompareRequest != null && File.Exists(_cliMgr.GetResultsPath(CompareRequest)) && !IsComparing;
    

    private void OpenResult()
    {
        if (!CanOpenResult()) return;

        Process process = new Process();
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

        _compareItems.Clear();
    }

    private bool CanCompareAsync() =>
        SelectedItem != null && !IsComparing;

    private async Task CompareAsync()
    {
        IDialogResult dr = await _dialogService.ShowDialogAsync("YesNoDialog", new DialogParameters("message=All excel processes will be terminated. " +
            "Did you save all your work?"));

        if (dr != null && dr.Result == ButtonResult.OK)
        {
            CompareRequest request = CompareRequest!;
            IsComparing = true;
            try
            {
                _dialogService.ShowDialog("YesNoDialog", new DialogParameters("message=Start comparing"));
                var result = await _cliMgr.CompareAsync(request);
                _dialogService.ShowDialog("YesNoDialog", new DialogParameters("message=Compare is done!"));
                _logger.Error("Compare tool success");
            }
            catch (Exception ex)
            {
                _logger.Error(ex, "Compare tool failed");
                _dialogService.ShowDialog("YesNoDialog", new DialogParameters("message=Compare was failed!"));
            }
            finally
            {
                IsComparing = false;
            }
        }
    }

    private bool CanOpenFileFromDialogReq()
    {
        return true;
    }

    private void OpenFileFromDialogReq()
    {
        if (!CanOpenFileFromDialogReq()) return;

        var dialog = new Microsoft.Win32.OpenFileDialog();
        dialog.FileName = "Excel File";
        dialog.DefaultExt = ".xlsx";
        dialog.Filter = "Excel files (.xlsx)|*.xlsx|All files (*.*)|*.*";
        bool? result = dialog.ShowDialog();
        if (result == true)
            DraftItem!.ReqPath = dialog.FileName;
    }

    private bool CanOpenFileToCompareFromDialog()
    {
        return true;
    }

    private void OpenFileToCompareFromDialog()
    {
        if (!CanOpenFileToCompareFromDialog()) return;
        var dialog = new Microsoft.Win32.OpenFileDialog();
        dialog.FileName = "File to Compare";
        dialog.DefaultExt = ".tar";
        dialog.Filter = "(.tar)|*.tar|(.xml)|*.xml|All files (*.*)|*.*";
        bool? result = dialog.ShowDialog();
        if (result == true)
            DraftItem!.ActualPath = dialog.FileName;
    }
}
