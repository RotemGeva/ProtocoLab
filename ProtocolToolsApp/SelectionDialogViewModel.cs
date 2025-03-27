using System.Collections.ObjectModel;
using System.Collections.Specialized;
using System.ComponentModel;

namespace ProtocoLab
{
    internal class SelectionDialogViewModel : DialogViewModelBase
    {
        private ObservableCollection<ProtocolItem> _protocols;
        private ObservableCollection<ProtocolItem> _filteredProtocols;
        private bool _hasSelectedItems;
        private string _filterText = string.Empty;

        public ObservableCollection<ProtocolItem> FilteredProtocols
        {
            get => _filteredProtocols;
            set => SetProperty(ref _filteredProtocols, value);
        }

        public ObservableCollection<ProtocolItem> Protocols
        {
            get => _protocols;
            set
            {
                if (SetProperty(ref _protocols, value))
                {
                    _protocols.CollectionChanged += Protocols_CollectionChanged;
                    foreach (var item in _protocols)
                        item.PropertyChanged += ProtocolItem_PropertyChanged;
                    
                    // Initialize filtered protocols with all items
                    FilteredProtocols = new ObservableCollection<ProtocolItem>(_protocols);
                }
            }
        }
        public bool HasSelectedItems
        {
            get => _hasSelectedItems;
            set => SetProperty(ref _hasSelectedItems, value);
        }

        public string FilterText
        {
            get => _filterText;
            set
            {
                if (SetProperty(ref _filterText, value))
                {
                    ApplyFilter();
                }
            }
        }

        public DelegateCommand ConfirmCommand { get; private set; }
        public DelegateCommand CancelCommand { get; private set; }

        public DelegateCommand SelectAllCommand { get; private set; }

        public DelegateCommand UnselectAllCommand { get; private set; }

        public SelectionDialogViewModel()
        {
            Title = "Protocols Selection";
            _protocols = new ObservableCollection<ProtocolItem>();
            _filteredProtocols = new ObservableCollection<ProtocolItem>();
            Protocols = _protocols;
            ConfirmCommand = new DelegateCommand(ConfirmDialog, CanConfirmDialog);
            CancelCommand = new DelegateCommand(CancelDialog);
            SelectAllCommand = new DelegateCommand(SelectAll);
            UnselectAllCommand = new DelegateCommand(UnselectAll);
        }


        public override void OnDialogOpened(IDialogParameters parameters)
        {
            if (parameters.ContainsKey("items"))
            {
                var protocolList = parameters.GetValue<List<string>>("items");
                Protocols = new ObservableCollection<ProtocolItem>(
                    protocolList.Select(p => new ProtocolItem { Name = p, IsSelected = false })
                );
            }
        }

        private void ApplyFilter()
        {
            if (string.IsNullOrWhiteSpace(_filterText))
            {
                // If filter is empty, show all items
                FilteredProtocols = new ObservableCollection<ProtocolItem>(_protocols);
            }
            else
            {
                FilteredProtocols = new ObservableCollection<ProtocolItem>(
                    _protocols.Where(p =>
                        p.Name.Contains(_filterText, StringComparison.OrdinalIgnoreCase)
                    )
                );
            }
        }

        private void ConfirmDialog()
        {
            var selectedProtocols = Protocols.Where(p => p.IsSelected).Select(p => p.Name).ToList();
            var result = new DialogResult(ButtonResult.OK);
            result.Parameters.Add("selectedItems", selectedProtocols);
            RaiseRequestClose(result);
        }

        private bool CanConfirmDialog()
        {
            return HasSelectedItems;
        }

        private void CancelDialog()
        {
            RaiseRequestClose(new DialogResult(ButtonResult.Cancel));
        }

        private void Protocols_CollectionChanged(object? sender, NotifyCollectionChangedEventArgs e)
        {
            switch (e.Action)
            {
                case NotifyCollectionChangedAction.Add:
                    foreach (ProtocolItem item in e.NewItems!)
                        item.PropertyChanged += ProtocolItem_PropertyChanged;
                    break;
                case NotifyCollectionChangedAction.Remove:
                    HasSelectedItems = Protocols.Any(p => p.IsSelected);
                    foreach (ProtocolItem item in e.OldItems!)
                        item.PropertyChanged -= ProtocolItem_PropertyChanged;
                    break;
                case NotifyCollectionChangedAction.Replace:
                case NotifyCollectionChangedAction.Move:
                case NotifyCollectionChangedAction.Reset:
                default:
                    break;
            }
            ConfirmCommand.RaiseCanExecuteChanged();
            ApplyFilter(); // Re-apply the filter after the collection is changed.
        }

        private void ProtocolItem_PropertyChanged(object? sender, PropertyChangedEventArgs e)
        {
            switch (e.PropertyName)
            {
                case nameof(ProtocolItem.IsSelected):
                    HasSelectedItems = Protocols.Any(p => p.IsSelected);
                    ConfirmCommand.RaiseCanExecuteChanged();
                    break;
            }
        }

        private void SelectAll()
        {
            foreach(var item in  FilteredProtocols)
                item.IsSelected = true;
        }

        private void UnselectAll()
        {
            foreach (var item in FilteredProtocols)
                item.IsSelected = false;
        }
    }

    public class ProtocolItem : BindableBase
    {
        private string? _name;
        public string Name
        {
            get => _name!;
            set => SetProperty(ref _name, value);
        }

        private bool _isSelected;
        public bool IsSelected
        {
            get => _isSelected;
            set => SetProperty(ref _isSelected, value);
        }
    }
}