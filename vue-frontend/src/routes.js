import Home from './components/HomeComponent.vue';
import Settings from './components/SettingsComponent.vue';
import PanelStreams from './components/PanelStreamsComponent.vue';
import PlaybackComponent from './components/PlaybackComponent.vue';
import DownloadComponent from './components/DownloadComponent.vue';
import FleetManagement from './components/FleetManagementComponent.vue';

const routes = [
    { name: 'Home', path: '/', component: Home },
    { name: 'Streams Panel', path: '/panelstreams', component: PanelStreams, icon: 'mdi-solar-panel-large' },
    { name: 'Settings', path: '/settings', component: Settings, icon: 'mdi-cog' },
    { name: 'Playback Videos', path: '/playback', component: PlaybackComponent, icon: 'mdi-video' },
    { name: 'Download Videos', path: '/download', component: DownloadComponent, icon: 'mdi-download' },
    { name: 'Fleet Management', path: '/fleetmanagement', component: FleetManagement, icon: 'mdi-truck' },
];

export default routes;
