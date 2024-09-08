namespace CompareCli;

public class CompareCliModule : IModule
{
    public void OnInitialized(IContainerProvider containerProvider)
    {
    }

    public void RegisterTypes(IContainerRegistry containerRegistry)
    {
        containerRegistry.RegisterSingleton<CompareCliApi.CliMgr>();
    }
}
