#pragma once

typedef enum {
    // Events with _ are unused, kept for compatibility
    DesktopMainEventLockWithPin,
    DesktopMainEventOpenLockMenu,
    DesktopMainEventOpenArchive,
    _DesktopMainEventOpenFavoriteLeftShort,
    _DesktopMainEventOpenFavoriteLeftLong,
    _DesktopMainEventOpenFavoriteRightShort,
    _DesktopMainEventOpenFavoriteRightLong,
    DesktopMainEventOpenMenu,
    _DesktopMainEventOpenDebug,
    DesktopMainEventOpenPowerOff,

    _DesktopDummyEventOpenLeft,
    _DesktopDummyEventOpenDown,
    _DesktopDummyEventOpenOk,

    DesktopLockedEventUnlocked,
    DesktopLockedEventUpdate,
    DesktopLockedEventShowPinInput,
    DesktopLockedEventCoversClosed,

    DesktopPinInputEventResetWrongPinLabel,
    DesktopPinInputEventUnlocked,
    DesktopPinInputEventUnlockFailed,
    DesktopPinInputEventBack,

    DesktopPinTimeoutExit,

    _DesktopDebugEventDeed,
    _DesktopDebugEventWrongDeed,
    _DesktopDebugEventSaveState,
    _DesktopDebugEventExit,

    DesktopLockMenuEventLockPinCode,
    DesktopLockMenuEventDummyModeOn,
    DesktopLockMenuEventDummyModeOff,
    DesktopLockMenuEventStealthModeOn,
    DesktopLockMenuEventStealthModeOff,

    DesktopAnimationEventCheckAnimation,
    DesktopAnimationEventNewIdleAnimation,
    DesktopAnimationEventInteractAnimation,

    DesktopSlideshowCompleted,
    DesktopSlideshowPoweroff,

    DesktopHwMismatchExit,

    DesktopEnclaveExit,

    DesktopBootTextExit,

    // Global events
    DesktopGlobalBeforeAppStarted,
    DesktopGlobalAfterAppFinished,
    DesktopGlobalAutoLock,
    DesktopGlobalApiUnlock,
    DesktopGlobalSaveSettings,
    DesktopGlobalReloadSettings,

    DesktopMainEventLockKeypad,
    DesktopLockedEventOpenPowerOff,
    DesktopLockMenuEventSettings,
    DesktopLockMenuEventLockKeypad,
    DesktopLockMenuEventLockPinOff,
    DesktopLockMenuEventMomentum,
    DesktopLockMenuEventScreenSettings,
} DesktopEvent;
