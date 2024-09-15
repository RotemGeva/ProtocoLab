using System.Collections.ObjectModel;

namespace ProtocoLab
{
    internal class SelectionDialogViewModel : DialogViewModelBase
    {
        private string _selectedProtocol;
        public ObservableCollection<string> Items { get; private set; }

        public string SelectedProtocol
        {
            get => _selectedProtocol;
            set => SetProperty(ref _selectedProtocol, value);
        }

        public DelegateCommand ConfirmCommand { get; set; }
        public DelegateCommand CancelCommand { get; set; }

        public SelectionDialogViewModel()
        {
            Title = "Protocols Selection";

            ConfirmCommand = new DelegateCommand(ConfirmDialog);
            CancelCommand = new DelegateCommand(CancelDialog);
        }

        public override void OnDialogOpened(IDialogParameters parameters)
        {
            if (parameters.ContainsKey("items"))
            {
                var items = parameters.GetValue<List<string>>("items");
                Items = new ObservableCollection<string>(items);
                RaisePropertyChanged(nameof(Items));
            }
        }

        private void ConfirmDialog()
        {
            // Pass the selected protocol back to the main window
            var parameters = new DialogParameters
            {
                { "SelectedProtocol", SelectedProtocol }
            };
            //RaiseRequestClose(new DialogResult(ButtonResult.OK, parameters));
        }

        private void CancelDialog()
        {
            RaiseRequestClose(new DialogResult(ButtonResult.Cancel));
        }
    }
}
