using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ProtocolToolsApp;

internal class YesNoDialogViewModel: DialogViewModelBase
{
    private string? _message;
    public string? Message
    {
        get { return _message; }
        set { SetProperty(ref _message, value); }
    }

    public DelegateCommand ConfirmCommand { get; set; }
    public DelegateCommand CancelCommand { get; set; }

    public YesNoDialogViewModel()
    {
        Title = "Confirm";
        ConfirmCommand = new DelegateCommand(ConfirmDialog);
        CancelCommand = new DelegateCommand(CancelDialog);
    }

    private void ConfirmDialog()
    {
        RaiseRequestClose(new DialogResult(ButtonResult.OK));
    }
    private void CancelDialog()
    {
        RaiseRequestClose(new DialogResult(ButtonResult.Cancel));
    }

    public override void OnDialogOpened(IDialogParameters parameters)
    {
        Message = parameters.GetValue<string>("message");
    }
}

