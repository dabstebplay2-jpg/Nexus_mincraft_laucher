APP_STYLE = r"""
* {
    font-family: "Segoe UI";
    color: #E5E7EB;
    font-size: 13px;
}

QMainWindow {
    background-color: #020617;
}

QWidget {
    background-color: transparent;
}

#AppContent {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #020617,
        stop:0.45 #071426,
        stop:1 #130B20
    );
}

QScrollArea {
    background: transparent;
    border: none;
}

QScrollBar:vertical {
    background: rgba(15, 23, 42, 130);
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: rgba(34, 197, 94, 160);
    border-radius: 5px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

/* SIDEBAR */

#Sidebar {
    background-color: rgba(2, 6, 23, 245);
    border-right: 1px solid rgba(148, 163, 184, 35);
}

#SidebarLogoCard {
    background-color: rgba(15, 23, 42, 210);
    border: 1px solid rgba(34, 197, 94, 90);
    border-radius: 22px;
}

#NexusMark {
    background-color: transparent;
    border-radius: 16px;
}

#NexusLogoTitle {
    color: #F8FAFC;
    font-size: 25px;
    font-weight: 900;
    letter-spacing: 3px;
}

#NexusLogoSubtitle {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
}

#SidebarSectionTitle {
    color: #64748B;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 3px;
    padding-left: 8px;
}

#SidebarNavButton {
    text-align: left;
    color: #CBD5E1;
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 14px;
    padding: 0 16px;
    font-size: 14px;
    font-weight: 800;
}

#SidebarNavButton:hover {
    background-color: rgba(34, 197, 94, 35);
    border: 1px solid rgba(34, 197, 94, 80);
    color: #F8FAFC;
}

#SidebarNavButton[active="true"] {
    background-color: rgba(34, 197, 94, 215);
    border: 1px solid #4ADE80;
    color: white;
}

#SidebarNavButton[disabledPage="true"] {
    color: #64748B;
}

#SidebarProfileCard {
    background-color: rgba(15, 23, 42, 220);
    border: 1px solid rgba(148, 163, 184, 55);
    border-radius: 18px;
}

#SidebarAvatar {
    background-color: transparent;
    border-radius: 14px;
}

#SidebarProfileName {
    color: #F8FAFC;
    font-size: 14px;
    font-weight: 900;
}

#SidebarProfileStatus {
    color: #86EFAC;
    font-size: 12px;
    font-weight: 700;
}

#SidebarProfileArrow {
    color: #94A3B8;
    font-size: 16px;
    font-weight: 900;
}

#SidebarIconButton {
    background-color: rgba(15, 23, 42, 190);
    border: 1px solid rgba(148, 163, 184, 45);
    border-radius: 12px;
    color: #CBD5E1;
    font-weight: 900;
}

#SidebarIconButton:hover {
    border: 1px solid #22C55E;
    color: #BBF7D0;
}

/* TOPBAR */

#Topbar {
    background-color: rgba(2, 6, 23, 220);
    border-bottom: 1px solid rgba(148, 163, 184, 35);
}

#TopbarTitle {
    color: #F8FAFC;
    font-size: 18px;
    font-weight: 900;
}

#TopbarSubtitle {
    color: #64748B;
    font-size: 12px;
    font-weight: 700;
}

#TopbarSearch {
    background-color: rgba(15, 23, 42, 220);
    border: 1px solid rgba(148, 163, 184, 55);
    border-radius: 14px;
    color: #F8FAFC;
    padding: 12px 16px;
    font-size: 14px;
}

#TopbarSearch:focus {
    border: 1px solid #22C55E;
}

#TopbarStatusButton {
    background-color: rgba(20, 83, 45, 160);
    border: 1px solid rgba(34, 197, 94, 130);
    border-radius: 14px;
    color: #BBF7D0;
    padding: 12px 18px;
    font-size: 13px;
    font-weight: 900;
}

#TopbarPlayButton {
    background-color: #22C55E;
    border: 1px solid #4ADE80;
    border-radius: 16px;
    color: white;
    padding: 13px 28px;
    font-size: 15px;
    font-weight: 900;
}

#TopbarPlayButton:hover {
    background-color: #16A34A;
}

/* GENERAL */

#PageTitle {
    color: #F8FAFC;
    font-size: 34px;
    font-weight: 900;
}

#PageDescription {
    color: #CBD5E1;
    font-size: 14px;
}

#Panel,
#DashboardPanel {
    background-color: rgba(15, 23, 42, 210);
    border: 1px solid rgba(148, 163, 184, 45);
    border-radius: 20px;
}

#DashboardPanel:hover,
#Panel:hover {
    border: 1px solid rgba(34, 197, 94, 95);
}

#PanelTitle {
    color: #F8FAFC;
    font-size: 18px;
    font-weight: 900;
}

#PanelText {
    color: #CBD5E1;
    font-size: 13px;
}

#EmptyText {
    color: #94A3B8;
    font-size: 14px;
    font-weight: 700;
}

#PrimaryButton {
    background-color: #22C55E;
    border: 1px solid #4ADE80;
    border-radius: 14px;
    color: white;
    padding: 11px 20px;
    font-weight: 900;
}

#PrimaryButton:hover {
    background-color: #16A34A;
}

#SecondaryButton {
    background-color: rgba(15, 23, 42, 190);
    border: 1px solid rgba(148, 163, 184, 60);
    border-radius: 14px;
    color: #CBD5E1;
    padding: 11px 20px;
    font-weight: 900;
}

#SecondaryButton:hover {
    border: 1px solid #22C55E;
    color: #BBF7D0;
}

#DangerButton {
    background-color: rgba(127, 29, 29, 180);
    color: #FEE2E2;
    border: 1px solid #EF4444;
    border-radius: 12px;
    padding: 10px 16px;
    font-weight: 800;
}

#DangerButton:hover {
    background-color: #DC2626;
    color: white;
}

#SearchInput {
    background-color: rgba(15, 23, 42, 210);
    border: 1px solid rgba(148, 163, 184, 55);
    border-radius: 14px;
    color: #F8FAFC;
    padding: 12px 16px;
}

#SearchInput:focus {
    border: 1px solid #22C55E;
}

QLineEdit,
QComboBox,
QTextEdit {
    background-color: rgba(15, 23, 42, 210);
    border: 1px solid rgba(148, 163, 184, 55);
    border-radius: 12px;
    color: #F8FAFC;
    padding: 10px 12px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #0F172A;
    color: #E5E7EB;
    selection-background-color: #22C55E;
    selection-color: white;
}

#BottomStatusBar {
    background-color: rgba(2, 6, 23, 230);
    border-top: 1px solid rgba(148, 163, 184, 35);
}

#BottomStatusText {
    color: #94A3B8;
    font-size: 12px;
}

/* HOME */

#MinecraftHero {
    border: 1px solid rgba(34, 197, 94, 90);
    border-radius: 26px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #071426,
        stop:0.38 #082B2B,
        stop:0.7 #0B3A26,
        stop:1 #14532D
    );
}

#HeroWelcome {
    color: #CBD5E1;
    font-size: 18px;
    font-weight: 700;
}

#HeroTitle {
    color: #F8FAFC;
    font-size: 52px;
    font-weight: 900;
}

#HeroSubtitle {
    color: #CBD5E1;
    font-size: 15px;
    font-weight: 700;
}

#HeroPlayButton {
    background-color: #22C55E;
    border: 1px solid #4ADE80;
    border-radius: 18px;
    color: #02130A;
    padding: 18px 42px;
    font-size: 20px;
    font-weight: 900;
}

#HeroPlayButton:hover {
    background-color: #4ADE80;
}

#HeroStatCard {
    background-color: rgba(15, 23, 42, 170);
    border: 1px solid rgba(34, 197, 94, 65);
    border-radius: 16px;
}

#HeroStatIcon {
    background-color: transparent;
}

#HeroStatTitle {
    color: #94A3B8;
    font-size: 12px;
    font-weight: 800;
}

#HeroStatValue {
    color: #F8FAFC;
    font-size: 14px;
    font-weight: 900;
}

#MiniProgress,
#BigProgress {
    background-color: rgba(15, 23, 42, 180);
    border: 1px solid rgba(148, 163, 184, 35);
    border-radius: 4px;
}

#MiniProgress::chunk,
#BigProgress::chunk {
    background-color: #22C55E;
    border-radius: 4px;
}

#InstanceDashboardRow,
#InstanceDashboardRowActive {
    background-color: rgba(15, 23, 42, 145);
    border: 1px solid rgba(148, 163, 184, 35);
    border-radius: 14px;
}

#InstanceDashboardRowActive {
    border: 1px solid #22C55E;
    background-color: rgba(20, 83, 45, 95);
}

#InstanceDashboardRow:hover {
    border: 1px solid rgba(34, 197, 94, 100);
}

#BlockIcon {
    background-color: transparent;
}

#InstanceTitle {
    color: #F8FAFC;
    font-size: 14px;
    font-weight: 900;
}

#InstanceMeta {
    color: #94A3B8;
    font-size: 12px;
    font-weight: 700;
}

#MiniPlayButton {
    background-color: rgba(34, 197, 94, 170);
    border: 1px solid rgba(34, 197, 94, 200);
    border-radius: 10px;
    color: white;
    font-weight: 900;
}

#SmallGhostButton,
#WideGhostButton,
#SquareGhostButton {
    background-color: rgba(15, 23, 42, 180);
    border: 1px solid rgba(148, 163, 184, 45);
    border-radius: 12px;
    color: #CBD5E1;
    padding: 8px 14px;
    font-weight: 800;
}

#SmallGhostButton:hover,
#WideGhostButton:hover,
#SquareGhostButton:hover {
    border: 1px solid #22C55E;
    color: #BBF7D0;
}

/* MODS / ACCOUNT */

#ModCard,
#AccountProviderCard,
#AccountCard {
    background-color: rgba(15, 23, 42, 175);
    border: 1px solid #243B2D;
    border-radius: 22px;
}

#ModCard:hover,
#AccountProviderCard:hover,
#AccountCard:hover {
    background-color: rgba(15, 35, 28, 210);
    border: 1px solid #22C55E;
}

#AccountCardSelected {
    background-color: rgba(22, 101, 52, 120);
    border: 1px solid #22C55E;
    border-radius: 18px;
}

#AccountProviderIcon,
#AccountAvatar,
#ModIconBox {
    background-color: rgba(34, 197, 94, 45);
    border: 1px solid #22C55E;
    border-radius: 16px;
    color: #BBF7D0;
    font-weight: 900;
}

#AccountStatusActive {
    background-color: rgba(34, 197, 94, 55);
    color: #BBF7D0;
    border: 1px solid #22C55E;
    border-radius: 10px;
    padding: 4px 10px;
    font-weight: 800;
}

#AccountEmptyState {
    background-color: rgba(15, 23, 42, 110);
    border: 1px dashed #31563D;
    border-radius: 22px;
    min-height: 220px;
}

#LogViewer {
    background-color: rgba(2, 6, 23, 220);
    border: 1px solid rgba(148, 163, 184, 45);
    border-radius: 16px;
    color: #E5E7EB;
    font-family: Consolas;
    font-size: 12px;
}
"""


APP_STYLE += r"""

/* SETTINGS FIX PACK */

#SettingsContent {
    background-color: transparent;
}

#SettingsRamValue {
    color: #22C55E;
    font-size: 22px;
    font-weight: 900;
}

#SettingsSectionLabel {
    color: #94A3B8;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 1px;
}

#SettingsStatCard {
    background-color: rgba(15, 23, 42, 165);
    border: 1px solid rgba(34, 197, 94, 65);
    border-radius: 16px;
}

#SettingsOptionsBox {
    background-color: rgba(2, 6, 23, 95);
    border: 1px solid rgba(148, 163, 184, 35);
    border-radius: 16px;
}

#RamPresetButton {
    background-color: rgba(15, 23, 42, 180);
    border: 1px solid rgba(148, 163, 184, 50);
    border-radius: 12px;
    color: #CBD5E1;
    padding: 9px 14px;
    font-weight: 900;
}

#RamPresetButton:hover {
    border: 1px solid #22C55E;
    color: #BBF7D0;
}

#RamPresetButton:disabled {
    color: #475569;
    border: 1px solid rgba(71, 85, 105, 70);
    background-color: rgba(15, 23, 42, 90);
}

#RamPresetButton[selected="true"] {
    background-color: rgba(34, 197, 94, 165);
    border: 1px solid #22C55E;
    color: white;
}

#SettingsCheckBox {
    color: #E5E7EB;
    font-weight: 800;
    spacing: 10px;
}

#SettingsCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid rgba(148, 163, 184, 80);
    background-color: rgba(15, 23, 42, 210);
}

#SettingsCheckBox::indicator:checked {
    background-color: #22C55E;
    border: 1px solid #4ADE80;
}

#RamSlider::groove:horizontal {
    height: 8px;
    background-color: rgba(15, 23, 42, 210);
    border: 1px solid rgba(148, 163, 184, 45);
    border-radius: 4px;
}

#RamSlider::sub-page:horizontal {
    background-color: #22C55E;
    border-radius: 4px;
}

#RamSlider::add-page:horizontal {
    background-color: rgba(15, 23, 42, 160);
    border-radius: 4px;
}

#RamSlider::handle:horizontal {
    background-color: #BBF7D0;
    border: 2px solid #22C55E;
    width: 20px;
    height: 20px;
    margin: -7px 0;
    border-radius: 10px;
}

#RamSlider::handle:horizontal:hover {
    background-color: white;
}

"""



APP_STYLE += r"""

/* FUNCTIONAL UI FIX PACK */

#InstanceCard {
    background-color: rgba(15, 23, 42, 195);
    border: 1px solid rgba(148, 163, 184, 45);
    border-radius: 20px;
}

#InstanceCard:hover {
    border: 1px solid rgba(34, 197, 94, 95);
}

#InstanceDetailHero {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(15, 23, 42, 230),
        stop:0.45 rgba(20, 83, 45, 180),
        stop:1 rgba(15, 23, 42, 210)
    );
    border: 1px solid rgba(34, 197, 94, 85);
    border-radius: 24px;
}

#InstanceDetailTabs::pane {
    background-color: rgba(15, 23, 42, 190);
    border: 1px solid rgba(148, 163, 184, 45);
    border-radius: 18px;
    padding: 8px;
}

#InstanceDetailTabs QTabBar::tab {
    background-color: rgba(15, 23, 42, 190);
    color: #CBD5E1;
    border: 1px solid rgba(148, 163, 184, 35);
    border-radius: 12px;
    padding: 10px 18px;
    margin-right: 8px;
    font-weight: 900;
}

#InstanceDetailTabs QTabBar::tab:selected {
    background-color: rgba(34, 197, 94, 180);
    border: 1px solid #22C55E;
    color: white;
}

#DetailInfoRow {
    background-color: rgba(2, 6, 23, 90);
    border: 1px solid rgba(148, 163, 184, 35);
    border-radius: 14px;
}

QProgressDialog {
    background-color: #0F172A;
    color: #E5E7EB;
}

QProgressDialog QLabel {
    color: #E5E7EB;
    font-weight: 800;
}

QProgressDialog QPushButton {
    background-color: rgba(15, 23, 42, 190);
    border: 1px solid rgba(148, 163, 184, 60);
    border-radius: 12px;
    color: #CBD5E1;
    padding: 8px 14px;
    font-weight: 900;
}

"""

APP_STYLE += r"""

/* SAFE MODRINTH PAGE */

#ModResultCard {
    background-color: rgba(15, 23, 42, 190);
    border: 1px solid rgba(148, 163, 184, 45);
    border-radius: 20px;
}

#ModResultCard:hover {
    border: 1px solid rgba(34, 197, 94, 95);
    background-color: rgba(15, 35, 28, 210);
}

#ModIconPlaceholder {
    background-color: rgba(34, 197, 94, 45);
    border: 1px solid rgba(34, 197, 94, 130);
    border-radius: 16px;
    color: #BBF7D0;
    font-size: 22px;
    font-weight: 900;
}

#ModTag {
    background-color: rgba(20, 83, 45, 105);
    border: 1px solid rgba(34, 197, 94, 100);
    border-radius: 10px;
    color: #BBF7D0;
    padding: 5px 10px;
    font-size: 11px;
    font-weight: 800;
}

"""

APP_STYLE += r"""

/* MODRINTH IMAGES AND DETAILS */

#ModResultCard {
    background-color: rgba(15, 23, 42, 190);
    border: 1px solid rgba(148, 163, 184, 45);
    border-radius: 20px;
}

#ModResultCard:hover {
    border: 1px solid rgba(34, 197, 94, 95);
    background-color: rgba(15, 35, 28, 210);
}

#ModIconImage,
#ModDetailsIcon {
    background-color: rgba(34, 197, 94, 45);
    border: 1px solid rgba(34, 197, 94, 130);
    border-radius: 16px;
    color: #BBF7D0;
    font-size: 22px;
    font-weight: 900;
}

#ModScreenshot {
    background-color: rgba(2, 6, 23, 160);
    border: 1px solid rgba(148, 163, 184, 50);
    border-radius: 14px;
    color: #94A3B8;
}

#ModTag {
    background-color: rgba(20, 83, 45, 105);
    border: 1px solid rgba(34, 197, 94, 100);
    border-radius: 10px;
    color: #BBF7D0;
    padding: 5px 10px;
    font-size: 11px;
    font-weight: 800;
}

#ModDescriptionBox {
    background-color: rgba(2, 6, 23, 180);
    border: 1px solid rgba(148, 163, 184, 45);
    border-radius: 14px;
    color: #E5E7EB;
    padding: 12px;
    font-size: 13px;
}

"""

APP_STYLE += r"""
/* NEXUS SKIN STUDIO 0.7.1 */
#SkinCard {
    background-color: rgba(15, 26, 46, 0.92);
    border: 1px solid rgba(36, 212, 107, 0.22);
    border-radius: 18px;
}
#SkinCard:hover {
    border: 1px solid rgba(36, 212, 107, 0.62);
    background-color: rgba(18, 45, 42, 0.92);
}
#AccountRow, #AccountRowActive {
    background-color: rgba(15, 26, 46, 0.88);
    border: 1px solid rgba(124, 155, 190, 0.20);
    border-radius: 16px;
}
#AccountRowActive {
    border: 1px solid rgba(36, 212, 107, 0.85);
    background-color: rgba(11, 54, 38, 0.88);
}
#MiniCard {
    background-color: rgba(15, 26, 46, 0.72);
    border: 1px solid rgba(124, 155, 190, 0.18);
    border-radius: 16px;
}
#SmallBadge {
    color: #8affb9;
    background-color: rgba(36, 212, 107, 0.14);
    border: 1px solid rgba(36, 212, 107, 0.34);
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 800;
}
#DangerButton {
    background-color: rgba(70, 22, 31, 0.55);
    border: 1px solid rgba(255, 92, 122, 0.38);
    border-radius: 12px;
    color: #ffd5dd;
    font-weight: 800;
    padding: 10px 14px;
}
#DangerButton:hover {
    background-color: rgba(120, 32, 48, 0.75);
    border: 1px solid rgba(255, 92, 122, 0.85);
}
"""


APP_STYLE += r"""
/* NEXUS DOWNLOADS CENTER 0.7.2 */

#DownloadSummaryCard {
    background-color: rgba(15, 26, 46, 0.88);
    border: 1px solid rgba(36, 212, 107, 0.22);
    border-radius: 18px;
}

#DownloadBigNumber {
    color: #8affb9;
    font-size: 34px;
    font-weight: 900;
}

#DownloadTaskCard,
#DownloadTaskCardActive {
    background-color: rgba(15, 26, 46, 0.90);
    border: 1px solid rgba(124, 155, 190, 0.20);
    border-radius: 18px;
}

#DownloadTaskCardActive {
    border: 1px solid rgba(36, 212, 107, 0.72);
    background-color: rgba(10, 45, 36, 0.92);
}

#DownloadIcon {
    background-color: rgba(36, 212, 107, 0.14);
    border: 1px solid rgba(36, 212, 107, 0.44);
    border-radius: 16px;
    color: #8affb9;
    font-size: 24px;
    font-weight: 900;
}

#DownloadStatus {
    color: #cfe9ff;
    font-size: 12px;
    font-weight: 700;
}

#DownloadError {
    color: #ffb4c3;
    background-color: rgba(80, 20, 34, 0.35);
    border: 1px solid rgba(255, 92, 122, 0.28);
    border-radius: 12px;
    padding: 10px;
}

#DownloadProgress {
    background-color: rgba(5, 10, 22, 0.8);
    border: 1px solid rgba(124, 155, 190, 0.18);
    border-radius: 4px;
}

#DownloadProgress::chunk {
    background-color: #24d46b;
    border-radius: 4px;
}
"""


APP_STYLE += r"""
/* REAL DOWNLOADS PAGE FIX */

#DownloadSummaryCard {
    background-color: rgba(15, 26, 46, 0.88);
    border: 1px solid rgba(36, 212, 107, 0.22);
    border-radius: 18px;
}

#DownloadBigNumber {
    color: #8affb9;
    font-size: 34px;
    font-weight: 900;
}

#DownloadTaskCard,
#DownloadTaskCardActive {
    background-color: rgba(15, 26, 46, 0.90);
    border: 1px solid rgba(124, 155, 190, 0.20);
    border-radius: 18px;
}

#DownloadTaskCardActive {
    border: 1px solid rgba(36, 212, 107, 0.72);
    background-color: rgba(10, 45, 36, 0.92);
}

#DownloadIcon {
    background-color: rgba(36, 212, 107, 0.14);
    border: 1px solid rgba(36, 212, 107, 0.44);
    border-radius: 16px;
    color: #8affb9;
    font-size: 24px;
    font-weight: 900;
}

#DownloadStatus {
    color: #cfe9ff;
    font-size: 12px;
    font-weight: 700;
}

#DownloadError {
    color: #ffb4c3;
    background-color: rgba(80, 20, 34, 0.35);
    border: 1px solid rgba(255, 92, 122, 0.28);
    border-radius: 12px;
    padding: 10px;
}

#DownloadProgress {
    background-color: rgba(5, 10, 22, 0.8);
    border: 1px solid rgba(124, 155, 190, 0.18);
    border-radius: 4px;
}

#DownloadProgress::chunk {
    background-color: #24d46b;
    border-radius: 4px;
}
"""
