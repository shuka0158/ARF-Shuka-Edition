#include "menu.h"

#include <gui/elements.h>
#include <assets_icons.h>
#include <furi.h>
#include <m-array.h>

// ── Data structures ────────────────────────────────────────────────────────

struct Menu {
    View* view;
    FuriTimer* anim_timer; // slide animation ticker
};

typedef struct {
    const char* label;
    IconAnimation* icon;
    uint32_t index;
    MenuItemCallback callback;
    void* callback_context;
} MenuItem;

ARRAY_DEF(MenuItemArray, MenuItem, M_POD_OPLIST); //-V658

#define M_OPL_MenuItemArray_t() ARRAY_OPLIST(MenuItemArray, M_POD_OPLIST)

typedef struct {
    MenuItemArray_t items;
    size_t position;
    // appearance config (stored in model so draw callback can read them)
    bool scroll_loop;   // wraps at list ends
    bool scroll_anim;   // slide animation enabled
    bool layout_grid;   // 4-column icon grid instead of list
    // animation state
    int8_t anim_offset; // pixel offset for slide animation; goes ±22 → 0
} MenuModel;

// ── Forward declarations ───────────────────────────────────────────────────

static void menu_process_up(Menu* menu);
static void menu_process_down(Menu* menu);
static void menu_process_ok(Menu* menu);

// ── Grid constants ─────────────────────────────────────────────────────────

#define GRID_COLS       4
#define GRID_CELL_W     32  // 128 / 4
#define GRID_CELL_H     19  // floor(57 / 3); 57 px for icons, 7 px for label
#define GRID_ICON_X_OFF 9   // (32 - 14) / 2 — center 14 px icon horizontally
#define GRID_ICON_Y_OFF 2   // small top margin
#define GRID_LABEL_Y    63  // bottom of screen; draw with AlignBottom

// ── List draw ─────────────────────────────────────────────────────────────

static void menu_draw_list(Canvas* canvas, MenuModel* model) {
    size_t count = MenuItemArray_size(model->items);
    int8_t ofs = model->anim_offset;

    // Draw 5 candidate slots so the canvas clips naturally during animation.
    // Slot indices relative to selected: -2, -1, 0 (selected), +1, +2
    // Final y positions: -19, 3, 25, 47, 69  (spacing 22 px)
    for(int slot = -2; slot <= 2; slot++) {
        int base_y = 25 + slot * 22; // -19 to 69
        int draw_y = base_y + (int)ofs;

        // Skip items completely off screen
        if(draw_y + 14 < 0 || draw_y > 63) continue;

        int logical = (int)model->position + slot;
        if(model->scroll_loop) {
            // Wrap: add count to keep positive before modulo
            logical = ((logical % (int)count) + (int)count) % (int)count;
        } else {
            if(logical < 0 || logical >= (int)count) continue;
        }
        size_t idx = (size_t)logical;
        MenuItem* item = MenuItemArray_get(model->items, idx);

        canvas_set_font(canvas, slot == 0 ? FontPrimary : FontSecondary);
        canvas_draw_icon_animation(canvas, 4, draw_y, item->icon);
        canvas_draw_str(canvas, 22, draw_y + 11, item->label);
    }

    // Selection frame and scrollbar are always at fixed positions
    elements_frame(canvas, 0, 21, 128 - 5, 21);
    elements_scrollbar(canvas, model->position, count);
}

// ── Grid draw ─────────────────────────────────────────────────────────────

static void menu_draw_grid(Canvas* canvas, MenuModel* model) {
    size_t count = MenuItemArray_size(model->items);
    size_t pos   = model->position;

    // Which page of 12 items are we on?
    size_t page_size  = (size_t)(GRID_COLS * 3);
    size_t page_start = (pos / page_size) * page_size;

    for(size_t i = 0; i < page_size; i++) {
        size_t idx = page_start + i;
        if(idx >= count) break;

        MenuItem* item = MenuItemArray_get(model->items, idx);
        int col = (int)(i % GRID_COLS);
        int row = (int)(i / GRID_COLS);
        int x   = col * GRID_CELL_W;
        int y   = row * GRID_CELL_H;

        if(idx == pos) {
            canvas_draw_box(canvas, x, y, GRID_CELL_W, GRID_CELL_H - 1);
            canvas_set_color(canvas, ColorWhite);
            canvas_draw_icon_animation(canvas, x + GRID_ICON_X_OFF, y + GRID_ICON_Y_OFF, item->icon);
            canvas_set_color(canvas, ColorBlack);
        } else {
            canvas_draw_icon_animation(canvas, x + GRID_ICON_X_OFF, y + GRID_ICON_Y_OFF, item->icon);
        }
    }

    // Show selected item's name at the bottom
    if(count) {
        MenuItem* sel = MenuItemArray_get(model->items, pos);
        canvas_set_font(canvas, FontSecondary);
        // Horizontal line separator
        canvas_draw_line(canvas, 0, GRID_CELL_H * 3, 127, GRID_CELL_H * 3);
        size_t lw = canvas_string_width(canvas, sel->label);
        int lx = (int)(128 - lw) / 2;
        if(lx < 0) lx = 0;
        canvas_draw_str(canvas, lx, GRID_LABEL_Y, sel->label);
    }
}

// ── Common draw callback ───────────────────────────────────────────────────

static void menu_draw_callback(Canvas* canvas, void* _model) {
    MenuModel* model = _model;
    canvas_clear(canvas);

    if(!MenuItemArray_size(model->items)) {
        canvas_draw_str(canvas, 2, 32, "Empty");
        elements_scrollbar(canvas, 0, 0);
        return;
    }

    if(model->layout_grid) {
        menu_draw_grid(canvas, model);
    } else {
        menu_draw_list(canvas, model);
    }
}

// ── Input ──────────────────────────────────────────────────────────────────

static bool menu_input_callback(InputEvent* event, void* context) {
    Menu* menu = context;
    bool consumed = false;

    bool is_action = (event->type == InputTypeShort || event->type == InputTypeRepeat);

    bool grid = false;
    with_view_model(menu->view, MenuModel * m, { grid = m->layout_grid; }, false);

    if(grid) {
        // Grid mode: all four directions navigate cells; Back propagates normally
        if(is_action) {
            if(event->key == InputKeyUp) {
                consumed = true;
                // move up one row
                with_view_model(
                    menu->view,
                    MenuModel * model,
                    {
                        size_t count = MenuItemArray_size(model->items);
                        if(count) {
                            MenuItem* old_item = MenuItemArray_get(model->items, model->position);
                            icon_animation_stop(old_item->icon);

                            if(model->position >= (size_t)GRID_COLS) {
                                model->position -= GRID_COLS;
                            } else if(model->scroll_loop) {
                                model->position = count - 1;
                            }

                            MenuItem* new_item = MenuItemArray_get(model->items, model->position);
                            icon_animation_start(new_item->icon);
                        }
                    },
                    true);
            } else if(event->key == InputKeyDown) {
                consumed = true;
                with_view_model(
                    menu->view,
                    MenuModel * model,
                    {
                        size_t count = MenuItemArray_size(model->items);
                        if(count) {
                            MenuItem* old_item = MenuItemArray_get(model->items, model->position);
                            icon_animation_stop(old_item->icon);

                            if(model->position + GRID_COLS < count) {
                                model->position += GRID_COLS;
                            } else if(model->scroll_loop) {
                                model->position = 0;
                            }

                            MenuItem* new_item = MenuItemArray_get(model->items, model->position);
                            icon_animation_start(new_item->icon);
                        }
                    },
                    true);
            } else if(event->key == InputKeyLeft) {
                consumed = true;
                with_view_model(
                    menu->view,
                    MenuModel * model,
                    {
                        size_t count = MenuItemArray_size(model->items);
                        if(count) {
                            MenuItem* old_item = MenuItemArray_get(model->items, model->position);
                            icon_animation_stop(old_item->icon);

                            if(model->position > 0) {
                                model->position--;
                            } else if(model->scroll_loop) {
                                model->position = count - 1;
                            }

                            MenuItem* new_item = MenuItemArray_get(model->items, model->position);
                            icon_animation_start(new_item->icon);
                        }
                    },
                    true);
            } else if(event->key == InputKeyRight) {
                consumed = true;
                with_view_model(
                    menu->view,
                    MenuModel * model,
                    {
                        size_t count = MenuItemArray_size(model->items);
                        if(count) {
                            MenuItem* old_item = MenuItemArray_get(model->items, model->position);
                            icon_animation_stop(old_item->icon);

                            if(model->position < count - 1) {
                                model->position++;
                            } else if(model->scroll_loop) {
                                model->position = 0;
                            }

                            MenuItem* new_item = MenuItemArray_get(model->items, model->position);
                            icon_animation_start(new_item->icon);
                        }
                    },
                    true);
            } else if(event->key == InputKeyOk) {
                consumed = true;
                menu_process_ok(menu);
            }
        }
    } else {
        // List mode
        if(is_action) {
            if(event->key == InputKeyUp) {
                consumed = true;
                menu_process_up(menu);
            } else if(event->key == InputKeyDown) {
                consumed = true;
                menu_process_down(menu);
            } else if(event->key == InputKeyOk) {
                consumed = true;
                menu_process_ok(menu);
            }
        }
    }

    return consumed;
}

// ── Enter / exit ───────────────────────────────────────────────────────────

static void menu_enter(void* context) {
    Menu* menu = context;
    with_view_model(
        menu->view,
        MenuModel * model,
        {
            if(MenuItemArray_size(model->items)) {
                MenuItem* item = MenuItemArray_get(model->items, model->position);
                icon_animation_start(item->icon);
            }
        },
        false);
}

static void menu_exit(void* context) {
    Menu* menu = context;
    furi_timer_stop(menu->anim_timer);
    with_view_model(
        menu->view,
        MenuModel * model,
        {
            model->anim_offset = 0;
            if(MenuItemArray_size(model->items)) {
                MenuItem* item = MenuItemArray_get(model->items, model->position);
                icon_animation_stop(item->icon);
            }
        },
        false);
}

// ── Slide animation timer ─────────────────────────────────────────────────

static void menu_anim_timer_cb(void* context) {
    Menu* menu = context;
    bool stop = false;
    with_view_model(
        menu->view,
        MenuModel * model,
        {
            if(model->anim_offset > 0) {
                model->anim_offset -= 5;
                if(model->anim_offset <= 0) { model->anim_offset = 0; stop = true; }
            } else if(model->anim_offset < 0) {
                model->anim_offset += 5;
                if(model->anim_offset >= 0) { model->anim_offset = 0; stop = true; }
            } else {
                stop = true;
            }
        },
        true);
    if(stop) furi_timer_stop(menu->anim_timer);
}

// ── Allocation ─────────────────────────────────────────────────────────────

Menu* menu_alloc(void) {
    Menu* menu = malloc(sizeof(Menu));
    menu->view = view_alloc();
    view_set_context(menu->view, menu);
    view_allocate_model(menu->view, ViewModelTypeLocking, sizeof(MenuModel));
    view_set_draw_callback(menu->view, menu_draw_callback);
    view_set_input_callback(menu->view, menu_input_callback);
    view_set_enter_callback(menu->view, menu_enter);
    view_set_exit_callback(menu->view, menu_exit);

    menu->anim_timer = furi_timer_alloc(menu_anim_timer_cb, FuriTimerTypePeriodic, menu);

    with_view_model(
        menu->view,
        MenuModel * model,
        {
            MenuItemArray_init(model->items);
            model->position    = 0;
            model->scroll_loop = true;
            model->scroll_anim = false;
            model->layout_grid = false;
            model->anim_offset = 0;
        },
        true);

    return menu;
}

void menu_free(Menu* menu) {
    furi_check(menu);

    furi_timer_stop(menu->anim_timer);
    furi_timer_free(menu->anim_timer);

    menu_reset(menu);
    with_view_model(menu->view, MenuModel * model, { MenuItemArray_clear(model->items); }, false);
    view_free(menu->view);

    free(menu);
}

// ── Public API ─────────────────────────────────────────────────────────────

View* menu_get_view(Menu* menu) {
    furi_check(menu);
    return menu->view;
}

void menu_add_item(
    Menu* menu,
    const char* label,
    const Icon* icon,
    uint32_t index,
    MenuItemCallback callback,
    void* context) {
    furi_check(menu);
    furi_check(label);

    MenuItem* item = NULL;
    with_view_model(
        menu->view,
        MenuModel * model,
        {
            item = MenuItemArray_push_new(model->items);
            item->label = label;
            item->icon  = icon ? icon_animation_alloc(icon) : icon_animation_alloc(&A_Plugins_14);
            view_tie_icon_animation(menu->view, item->icon);
            item->index            = index;
            item->callback         = callback;
            item->callback_context = context;
        },
        true);
}

void menu_reset(Menu* menu) {
    furi_check(menu);
    furi_timer_stop(menu->anim_timer);
    with_view_model(
        menu->view,
        MenuModel * model,
        {
            model->anim_offset = 0;
            for
                M_EACH(item, model->items, MenuItemArray_t) {
                    icon_animation_stop(item->icon);
                    icon_animation_free(item->icon);
                }
            MenuItemArray_reset(model->items);
            model->position = 0;
        },
        true);
}

void menu_set_selected_item(Menu* menu, uint32_t index) {
    furi_check(menu);
    with_view_model(
        menu->view,
        MenuModel * model,
        {
            if(index < MenuItemArray_size(model->items)) {
                model->position = index;
            }
        },
        true);
}

void menu_set_scroll_loop(Menu* menu, bool enabled) {
    furi_check(menu);
    with_view_model(
        menu->view, MenuModel * model, { model->scroll_loop = enabled; }, false);
}

void menu_set_scroll_anim(Menu* menu, bool enabled) {
    furi_check(menu);
    with_view_model(
        menu->view, MenuModel * model, { model->scroll_anim = enabled; }, false);
}

void menu_set_layout_grid(Menu* menu, bool grid) {
    furi_check(menu);
    with_view_model(
        menu->view, MenuModel * model, { model->layout_grid = grid; }, true);
}

// ── List navigation ────────────────────────────────────────────────────────

static void menu_process_up(Menu* menu) {
    with_view_model(
        menu->view,
        MenuModel * model,
        {
            size_t count = MenuItemArray_size(model->items);
            if(count) {
                MenuItem* item = MenuItemArray_get(model->items, model->position);
                icon_animation_stop(item->icon);

                size_t old_pos = model->position;
                if(model->position > 0) {
                    model->position--;
                } else if(model->scroll_loop) {
                    model->position = count - 1;
                }

                item = MenuItemArray_get(model->items, model->position);
                icon_animation_start(item->icon);

                if(model->scroll_anim && model->position != old_pos) {
                    // Items slide DOWN (y increases) — offset starts negative
                    model->anim_offset = -22;
                    furi_timer_start(menu->anim_timer, 25);
                }
            }
        },
        true);
}

static void menu_process_down(Menu* menu) {
    with_view_model(
        menu->view,
        MenuModel * model,
        {
            size_t count = MenuItemArray_size(model->items);
            if(count) {
                MenuItem* item = MenuItemArray_get(model->items, model->position);
                icon_animation_stop(item->icon);

                size_t old_pos = model->position;
                if(model->position < count - 1) {
                    model->position++;
                } else if(model->scroll_loop) {
                    model->position = 0;
                }

                item = MenuItemArray_get(model->items, model->position);
                icon_animation_start(item->icon);

                if(model->scroll_anim && model->position != old_pos) {
                    // Items slide UP (y decreases) — offset starts positive
                    model->anim_offset = 22;
                    furi_timer_start(menu->anim_timer, 25);
                }
            }
        },
        true);
}

static void menu_process_ok(Menu* menu) {
    MenuItem* item = NULL;
    with_view_model(
        menu->view,
        MenuModel * model,
        {
            if(MenuItemArray_size(model->items)) {
                item = MenuItemArray_get(model->items, model->position);
            }
        },
        true);
    if(item && item->callback) {
        item->callback(item->callback_context, item->index);
    }
}
