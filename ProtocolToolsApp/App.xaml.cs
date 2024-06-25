using Serilog;
using Serilog.Events;
using System.Configuration;
using System.Data;
using System.Windows;
using static DryIoc.Setup;

namespace ProtocolToolsApp;

/// <summary>
/// Interaction logic for App.xaml
/// </summary>
public partial class App : PrismApplication
{
    protected override Window CreateShell() => Container.Resolve<MainWindow>();

    protected override void Initialize()
    {
        base.Initialize();

        LoggerConfiguration loggerConfiguration = new LoggerConfiguration()
        .Enrich.WithThreadId()
        .MinimumLevel.Is(LogEventLevel.Verbose);

        loggerConfiguration.WriteTo.File(
            path: "ProtocolTools.log",
            rollingInterval: RollingInterval.Day,
            rollOnFileSizeLimit: true,
            retainedFileCountLimit: 16);

        Log.Logger = loggerConfiguration.CreateLogger();

        var logger = Log.ForContext<App>();

        logger.Information("logging initialized");
    }

    protected override void RegisterTypes(IContainerRegistry containerRegistry)
    {
        ViewModelLocationProvider.Register<MainWindow, MainWindowViewModel>();
        containerRegistry.RegisterDialog<NotificationDialog, NotificationDialogViewModel>();
        containerRegistry.RegisterDialog<YesNoDialog, YesNoDialogViewModel>();
    }

    protected override void OnInitialized()
    {
        //var regionManager = Container.Resolve<IRegionManager>();

        //regionManager?.RegisterViewWithRegion(nameof(MainWindow), CoreUiViewName.MainView);

        base.OnInitialized();
    }
}
