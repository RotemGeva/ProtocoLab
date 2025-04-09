namespace ProtocoLab
{
    internal class ProgressDialogViewModel : DialogViewModelBase
    {

        private string? _message;
        private double _progress;
        public string? Message
        {
            get { return _message; }
            set { SetProperty(ref _message, value); }
        }

        public double Progress
        {
            get { return _progress; }
            set { SetProperty(ref _progress, value); }
        }

        public ProgressDialogViewModel()
        {
            Title = "Progress Dialog";
            Progress = 0;
            
        }

        public override void OnDialogOpened(IDialogParameters parameters)
        {
            var progressReporter = parameters["progressReporter"] as Progress<(double progress, string message)>;

            if (progressReporter != null)
            {
                progressReporter.ProgressChanged += (sender, progressData) =>
                {
                    Progress = progressData.progress;
                    if (Progress == 100)
                        CloseDialog();
                    Message = progressData.message;
                };
                
            }
        }

        private void CloseDialog()
        {
            RaiseRequestClose(new DialogResult(ButtonResult.OK));
        }
    }
}