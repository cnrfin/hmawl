/* Area tools, as the item descriptions intend (the GameCube build only ever hits one tile):
   Strange Hoe +, Weird Hoe 3x3, Strange Sickle - (across the facing), Weird Sickle +, Watering Can W 3x3.
   A tool use is two messages (tools/toolfix/NOTES.md):
   1. func_80043120 (A action) case 0xF: a type-1 hit (func_8004579C, message at r1+0x778, +0x10 target id) via
      func_80011680. The tile / grass only goes pending (field tile state 3 sub 1, grass state 1).
      pm_area_stub (0x8004390C, after that send) -> tool_area: re-send it to the neighbours, remember the ones
      that accepted (result 0).
   2. tool state 0x79, impact frame (lbl_80033130): a type-0x1C message to pl+0x1388 at 0x800332BC; that applies
      the till / water / cut and rebuilds the look. pm_impact_stub (0x800332C0) -> tool_area_impact: the same 0x1C
      to the remembered neighbours.
   Field tiles: ids 0x1A5..0x276, *(0x80349200)+0x4C stride 0x308 (+0x70 descriptor {w, h}, +0x74 g, +0x75 l;
   a = l / h (x), b = l % h (z)). Pasture grass: ids 0x278..0x4B3, a 26 (x) x 22 (z) grid, id = 0x278 + ix*22 + iz;
   only full-grown grass (growth >= 450, state 0) is cuttable. Stamina / skill / water are charged once. */
typedef unsigned char u8; typedef int s32; typedef unsigned int u32; typedef unsigned short u16;
#define F(addr, ret, args) ((ret (*) args)(addr))
#define msg_send   F(0x80011680, s32, (u8 *))
#define obj_by_id  F(0x8001075C, u8 *, (u8 *, s32))
#define NO_OBJ     ((u8 *)0x802E8EFC)
#define TILE_ID0   0x1A5
#define TILE_ID1   0x276
#define GRASS_ID0  0x278
#define GRASS_W    26
#define GRASS_H    22
#define OK(p)      ((u32)(p) >= 0x80000000u && (u32)(p) < 0x81800000u)
enum { NONE, PLUS, SQUARE, LINE };
static s32 pend_ids[8], pend_n, pend_main = -1;
static s32 shape_of(s32 item)
{
    switch (item) {
    case 0x4E1: case 0x4E9: return PLUS;        /* Strange Hoe, Weird Sickle */
    case 0x4E2: case 0x4EF: return SQUARE;      /* Weird Hoe, Watering Can W */
    case 0x4E8: return LINE;                    /* Strange Sickle */
    }
    return NONE;
}
static u8 *grass_obj(s32 id)                    /* pasture grass object, or 0 */
{
    u8 *rec, *ifc;
    if (id < GRASS_ID0 || id >= GRASS_ID0 + GRASS_W * GRASS_H) return 0;
    rec = obj_by_id(*(u8 **)0x80349230, id);
    if (!OK(rec) || rec == NO_OBJ) return 0;
    ifc = *(u8 **)(rec + 0x14);
    if (!OK(ifc) || *(s32 *)(ifc + 4) != id || *(s32 *)(ifc + 8) != 4) return 0;
    return ifc + *(s32 *)(ifc + 0x10) - 0xA8;
}
static s32 grass_ripe(u8 *o)                    /* state 0 and full grown, as the game's own targeting requires */
{
    u8 *gr = *(u8 **)0x803491CC + 0x14E84 + *(u16 *)(o + 0x72) * 8;
    return *(signed char *)(o + 0x70) == 0 && *(u16 *)(gr + 4) >= 0x1C2;
}
void tool_area(u8 *msg, s32 item, u8 *pl, s32 main_res)
{
    s32 id = *(s32 *)(msg + 0x10), shape = shape_of(item), a, b, w, h, base, da, db, nid;
    u8 *go = 0, *n;
    float fx, fz, ax, az;
    pend_n = 0; pend_main = -1;
    if (!shape || main_res != 0) return;        /* refused: the player won't swing, nothing would apply */
    if (id >= TILE_ID0 && id <= TILE_ID1) {
        u8 *mgr = *(u8 **)0x80349200, *obj; u32 *desc; s32 g, l;
        if (!OK(mgr)) return;
        obj = *(u8 **)(mgr + 0x4C) + (id - TILE_ID0) * 0x308;
        desc = *(u32 **)(obj + 0x70);
        if (!OK(desc)) return;
        w = (s32)desc[0]; h = (s32)desc[1]; g = obj[0x74]; l = obj[0x75];
        if (w <= 0 || h <= 0 || g != id - TILE_ID0) return;
        a = l / h; b = l % h; base = TILE_ID0 + (g - l);
    } else if ((go = grass_obj(id)) != 0) {
        w = GRASS_W; h = GRASS_H; base = GRASS_ID0; a = (id - base) / h; b = (id - base) % h;
    } else return;
    fx = *(float *)(pl + 0x58); fz = *(float *)(pl + 0x60);
    ax = fx < 0 ? -fx : fx; az = fz < 0 ? -fz : fz;
    for (da = -1; da <= 1; da++)
        for (db = -1; db <= 1; db++) {
            if (!da && !db) continue;
            if (shape == PLUS && da && db) continue;
            if (shape == LINE && (ax > az ? (da || !db) : (db || !da))) continue;   /* "-": beside the target */
            if (a + da < 0 || a + da >= w || b + db < 0 || b + db >= h) continue;
            nid = base + (a + da) * h + (b + db);
            if (go) {                               /* grass: right type and position, and ripe */
                float dx, dz;
                n = grass_obj(nid);
                if (!n || !grass_ripe(n)) continue;
                dx = *(float *)(n + 0x4C) - *(float *)(go + 0x4C) - da;
                dz = *(float *)(n + 0x54) - *(float *)(go + 0x54) - db;
                if (dx < -0.25f || dx > 0.25f || dz < -0.25f || dz > 0.25f) continue;
            }
            *(s32 *)(msg + 0x10) = nid;
            if (msg_send(msg) == 0 && pend_n < 8) pend_ids[pend_n++] = nid;
        }
    *(s32 *)(msg + 0x10) = id;
    if (pend_n) pend_main = id;
}
void tool_area_impact(u8 *msg, u8 *pl)          /* msg: the 0x1C the game just sent to pl+0x1388 */
{
    s32 i, id = *(s32 *)(msg + 0x10);
    if (pend_n && id == pend_main && *(s32 *)(pl + 0x1388) == id && *(s32 *)(msg + 4) == 0x1C)
        for (i = 0; i < pend_n; i++) { *(s32 *)(msg + 0x10) = pend_ids[i]; msg_send(msg); }
    *(s32 *)(msg + 0x10) = id;
    pend_n = 0; pend_main = -1;
}

/* New game (pm_newgame_stub, after the Milker is given): the Stick goes in the rucksack the same way.
   A WEAPONS_ALL build (testing) gives the three swords as well. */
#define item_pool_add F(0x8004FDA0, void, (u8 *, s32, s32, s32))
void newgame_extra(u8 *g)
{
    item_pool_add(g + 0x50, 0x4E3, 1, -1);          /* Stick */
#ifdef WEAPONS_ALL
    item_pool_add(g + 0x50, 0x4E4, 1, -1);          /* Wooden Sword */
    item_pool_add(g + 0x50, 0x4EA, 1, -1);          /* Farmer's Sword */
    item_pool_add(g + 0x50, 0x4EB, 1, -1);          /* H.M Murasama */
#endif
}
