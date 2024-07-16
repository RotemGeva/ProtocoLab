using Prism.Mvvm;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Prism.Dialogs;

namespace ProtocolsToolApp;

internal class DialogViewModelBase : BindableBase, IDialogAware
{
    private string? _iconSource;
    public string? IconSource
    {
        get { return _iconSource; }
        set { SetProperty(ref _iconSource, value); }
    }

    private string? _title;
    public string? Title
    {
        get { return _title; }
        set { SetProperty(ref _title, value); }
    }


    public DialogCloseListener RequestClose { get; }

    public virtual void RaiseRequestClose(IDialogResult dialogResult)
    {
        RequestClose.Invoke(dialogResult);
    }

    public virtual bool CanCloseDialog()
    {
        return true;
    }

    public virtual void OnDialogClosed()
    {
    }

    public virtual void OnDialogOpened(IDialogParameters parameters)
    {
    }
}