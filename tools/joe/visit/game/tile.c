/* Field tile cursor in the Z-target reticle's style. The game draws the highlighted tile with
   func_80091F58(pos, view mtx): a 1-pixel yellow line square (u8 corners 0x8024FBE0, colour 0x8024FC00
   F1F50F / F3) at (pos.x - 0.5, pos.y + 0.05, pos.z - 0.5). HOOK18 sends it here instead: four flat yellow
   corner brackets lying on the tile (quads, both windings), settling in (slightly larger, no bounce) when the
   cursor moves to another tile and pulsing gently, like the lock-on brackets (zt.c). Same GX set-up as the original. */
typedef unsigned int u32;
typedef int s32;
typedef unsigned char u8;
#define F(addr, ret, args) ((ret (*) args)(addr))
#define GXSetBlendMode    F(0x801D1E70, void, (s32, s32, s32, s32))
#define GXClearVtxDesc    F(0x801CD0C8, void, (void))
#define GXSetVtxDesc      F(0x801CCC7C, void, (s32, s32))
#define GXSetVtxAttrFmt   F(0x801CD100, void, (s32, s32, s32, s32, s32))
#define GXSetNumChans     F(0x801CF624, void, (s32))
#define GXSetChanCtrl     F(0x801CF660, void, (s32, s32, s32, s32, s32, s32, s32))
#define GXSetNumTexGens   F(0x801CD994, void, (s32))
#define GXSetNumTevStages F(0x801D1950, void, (s32))
#define GXSetTevOrder     F(0x801D17B4, void, (s32, s32, s32, s32))
#define GXSetTevOp        F(0x801D1214, void, (s32, s32))
#define PSMTXTrans        F(0x801B82B0, void, (float *, float, float, float))
#define PSMTXConcat       F(0x801B7D6C, void, (const float *, const float *, float *))
#define GXLoadPosMtxImm   F(0x801D2668, void, (const float *, s32))
#define GXSetCurrentMtx   F(0x801D2708, void, (s32))
#define GXBegin           F(0x801CE2CC, void, (s32, s32, s32))
#define WGP_F (*(volatile float *)0xCC008000)
#define WGP_U (*(volatile u32 *)0xCC008000)
#define TC_COL   0xFFCE2EF0u        /* the reticle's yellow (255, 206, 46), alpha as the original's */
#define TC_HALF  0.46f              /* bracket box half-size (the tile is 1 x 1) */
#define TC_ARM   0.26f
#define TC_W     0.07f              /* bar width */
#define TC_SNAP  6.0f               /* frames to settle from 1.15x (test 15's bounce from 1.6x was too much) */
static float tsin(float x)
{
    float x2;
    while (x > 3.14159274f) x -= 6.28318548f;
    while (x < -3.14159274f) x += 6.28318548f;
    x2 = x * x;
    return x * (1 - x2 / 6 * (1 - x2 / 20 * (1 - x2 / 42)));
}
static struct { float x, z; u32 t; } TC;
static void vtx(float x, float z) { WGP_F = x; WGP_F = 0; WGP_F = z; WGP_U = TC_COL; }
static void bar(float x0, float z0, float x1, float z1)
{
    vtx(x0, z0); vtx(x1, z0); vtx(x1, z1); vtx(x0, z1);       /* one winding ... */
    vtx(x0, z0); vtx(x0, z1); vtx(x1, z1); vtx(x1, z0);       /* ... and the other (no culling either way) */
}
void zt_tile_cursor(const float *pos, const float *view)
{
    float m[12], h, H, A, t;
    s32 sx, sz;
    if (pos[0] != TC.x || pos[2] != TC.z) { TC.x = pos[0]; TC.z = pos[2]; TC.t = 0; }   /* a new tile: snap in */
    t = (float)TC.t; if (TC.t < 100000) TC.t++;
    if (t < TC_SNAP) { float u = 1 - t / TC_SNAP; h = 1.0f + 0.15f * u * u * u; }   /* small settle, no overshoot */
    else h = 1.0f + 0.04f * tsin((t - TC_SNAP) * (6.28318548f / 42.0f));
    H = TC_HALF * h; A = TC_ARM * h;
    GXSetBlendMode(1, 4, 5, 0);
    GXClearVtxDesc();
    GXSetVtxDesc(9, 1); GXSetVtxDesc(0xB, 1);               /* position, colour: direct */
    GXSetVtxAttrFmt(0, 9, 1, 4, 0);                         /* xyz f32 */
    GXSetVtxAttrFmt(0, 0xB, 1, 5, 0);                       /* rgba8 */
    GXSetNumChans(1);
    GXSetChanCtrl(4, 0, 0, 1, 0, 0, 2);
    GXSetNumTexGens(0);
    GXSetNumTevStages(1);
    GXSetTevOrder(0, 0xFF, 0xFF, 4);
    GXSetTevOp(0, 4);
    PSMTXTrans(m, pos[0], pos[1] + 0.05f, pos[2]);
    PSMTXConcat(view, m, m);
    GXLoadPosMtxImm(m, 0);
    GXSetCurrentMtx(0);
    GXBegin(0x80, 0, 64);                                   /* quads: 8 bars x 2 windings */
    for (sx = -1; sx <= 1; sx += 2)
        for (sz = -1; sz <= 1; sz += 2) {
            float cx = sx * H, cz = sz * H;
            bar(cx - sx * A, cz - sz * TC_W, cx, cz);          /* arm along x */
            bar(cx - sx * TC_W, cz - sz * A, cx, cz);          /* arm along z */
        }
    GXSetBlendMode(0, 1, 0, 0);
}
