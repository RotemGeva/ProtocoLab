using System.Collections.ObjectModel;
using System.Collections.Specialized;

namespace ProtocoLab
{
    internal class SelectionDialogViewModel : DialogViewModelBase
    {
        private ObservableCollection<ProtocolItem> _protocols;
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

        public DelegateCommand ConfirmCommand { get; private set; }
        public DelegateCommand CancelCommand { get; private set; }

        public DelegateCommand SelectAllCommand { get; private set; }

        public SelectionDialogViewModel()
        {
            Title = "Protocols Selection";
            Protocols = new ObservableCollection<ProtocolItem>();
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
            return Protocols.Any(p => p.IsSelected);
        }

        private void CancelDialog()
        {
            RaiseRequestClose(new DialogResult(ButtonResult.Cancel));
        }

        private void Protocols_CollectionChanged(object sender, NotifyCollectionChangedEventArgs e)
        {
            if (e.NewItems != null)
            {
                foreach (ProtocolItem item in e.NewItems)
                    item.PropertyChanged += ProtocolItem_PropertyChanged;
            }
            if (e.OldItems != null)
            {
                foreach (ProtocolItem item in e.OldItems)
                    item.PropertyChanged -= ProtocolItem_PropertyChanged;
            }
            ConfirmCommand.RaiseCanExecuteChanged();
        }

        private void ProtocolItem_PropertyChanged(object sender, System.ComponentModel.PropertyChangedEventArgs e)
        {
            if (e.PropertyName == nameof(ProtocolItem.IsSelected))
            {
                ConfirmCommand.RaiseCanExecuteChanged();
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