/* Area tools, as the item descriptions intend (the GameCube build only ever hits one tile):
   Strange Hoe +, Weird Hoe 3x3, Strange Sickle - (across the facing), Weird Sickle +, Watering Can W 3x3.
   func_80043120 (A-button action), case 0xF (hoe / sickle / can on a field tile) builds one tool-hit message
   (func_8004579C: +4 type 1, +8 water flag, +0xC item, +0x10 target id) at r1+0x778 and sends it with
   func_80011680. pm_area_stub (hooked at 0x8004390C, right after that send) calls tool_area, which re-sends the
   same message to the neighbouring tiles. Field tiles are 210 permanent objects (id 0x1A5 + global index) in
   *(0x80349200)+0x4C, stride 0x308: +0x70 field descriptor {w, h, ..}, +0x74 global index, +0x75 local index l,
   a = l / h (x), b = l % h (z). Each tile's own handler accepts or ignores the hit; stamina, skill and water are
   charged once by the player's tool state, not per message (tools/toolfix/NOTES.md). */
typedef unsigned char u8; typedef int s32; typedef unsigned int u32;
#define F(addr, ret, args) ((ret (*) args)(addr))
#define msg_send   F(0x80011680, s32, (u8 *))
#define TILE_ID0   0x1A5
#define TILE_ID1   0x276
enum { NONE, PLUS, SQUARE, LINE };
static s32 shape_of(s32 item)
{
    switch (item) {
    case 0x4E1: case 0x4E9: return PLUS;        /* Strange Hoe, Weird Sickle */
    case 0x4E2: case 0x4EF: return SQUARE;      /* Weird Hoe, Watering Can W */
    case 0x4E8: return LINE;                    /* Strange Sickle */
    }
    return NONE;
}
void tool_area(u8 *msg, s32 item, u8 *pl)
{
    s32 id = *(s32 *)(msg + 0x10), shape = shape_of(item), a, b, w, h, g, l, da, db;
    u8 *mgr, *obj; u32 *desc;
    float fx, fz;
    if (!shape || id < TILE_ID0 || id > TILE_ID1) return;
    mgr = *(u8 **)0x80349200;
    if ((u32)mgr < 0x80000000u || (u32)mgr >= 0x81800000u) return;
    obj = *(u8 **)(mgr + 0x4C) + (id - TILE_ID0) * 0x308;
    desc = *(u32 **)(obj + 0x70);
    if ((u32)desc < 0x80000000u || (u32)desc >= 0x81800000u) return;
    w = (s32)desc[0]; h = (s32)desc[1]; g = obj[0x74]; l = obj[0x75];
    if (w <= 0 || h <= 0 || g != id - TILE_ID0) return;
    a = l / h; b = l % h;
    fx = *(float *)(pl + 0x58); fz = *(float *)(pl + 0x60);
    for (da = -1; da <= 1; da++)
        for (db = -1; db <= 1; db++) {
            if (!da && !db) continue;
            if (shape == PLUS && da && db) continue;
            if (shape == LINE) {                        /* "-": the two tiles beside the target, across the facing */
                float ax = fx < 0 ? -fx : fx, az = fz < 0 ? -fz : fz;
                if (ax > az ? (da || !db) : (db || !da)) continue;
            }
            if (a + da < 0 || a + da >= w || b + db < 0 || b + db >= h) continue;
            *(s32 *)(msg + 0x10) = TILE_ID0 + (g - l) + (a + da) * h + (b + db);
            msg_send(msg);
        }
    *(s32 *)(msg + 0x10) = id;
}
