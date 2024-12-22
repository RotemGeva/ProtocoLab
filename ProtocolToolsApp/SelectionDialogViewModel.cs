using System.Collections.ObjectModel;
using System.Collections.Specialized;
using System.ComponentModel;

namespace ProtocoLab
{
    internal class SelectionDialogViewModel : DialogViewModelBase
    {
        private ObservableCollection<ProtocolItem> _protocols;
        private bool _hasSelectedItems;
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
                }
            }
        }
        public bool HasSelectedItems
        {
            get => _hasSelectedItems;
            set => SetProperty(ref _hasSelectedItems, value);
        }

        public DelegateCommand ConfirmCommand { get; private set; }
        public DelegateCommand CancelCommand { get; private set; }

        public DelegateCommand SelectAllCommand { get; private set; }

        public SelectionDialogViewModel()
        {
            Title = "Protocols Selection";
            _protocols = new ObservableCollection<ProtocolItem>();
            Protocols = _protocols;
            ConfirmCommand = new DelegateCommand(ConfirmDialog, CanConfirmDialog);
            CancelCommand = new DelegateCommand(CancelDialog);
            SelectAllCommand = new DelegateCommand(SelectAll);
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
            foreach(var item in  _protocols)
                item.IsSelected = true;
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