using Prism.Commands;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ProtocoLab;

internal class NotificationDialogViewModel : DialogViewModelBase
{
    private string? _message;
    public string? Message
    {
        get { return _message; }
        set { SetProperty(ref _message, value); }
    }

    public DelegateCommand CloseDialogCommand { get; set; }

    public NotificationDialogViewModel()
    {
        Title = "Notification";
        CloseDialogCommand = new DelegateCommand(CloseDialog);
    }

    private void CloseDialog()
    {
        RaiseRequestClose(new DialogResult(ButtonResult.OK));
    }

    public override void OnDialogOpened(IDialogParameters parameters)
    {
        Message = parameters.GetValue<string>("message");
    }
}