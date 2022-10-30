#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# file  : svp.vpy
# author: lo
# python3.* is needed for vapoursynth

import platform

import vapoursynth as vs
from vapoursynth import core

core.num_threads = 8
core.max_cache_size = 8192

clip = video_in

# source & display video fps
svf = container_fps or 23.976
dpf = display_fps   or 59.970

def getMWH(pf):
    if "Windows" in pf:
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    else:
        from subprocess import check_output
        if "Linux" in pf:
            # test in ubuntu
            command = "xrandr | awk -F' ' '/\*/{print $1}'"
        elif "MacOS" in pf:
            # test for python3 in catalina
            command = "system_profiler SPDisplaysDataType | awk -F' ' '/Resolution/{print $2 \"x\" $4}'"
        else:
            return 1920, 1080
    return check_output(command, shell=True, encoding="utf-8").strip().split("x")

if dpf - svf > 10:
    abs = True
    target_fps = 60

    # video width & height
    vw, vh = video_in_dw, video_in_dh
    # screen/monitor width & height
    mw, mh = getMWH(platform.system())

    num = round(min(max(target_fps, svf * 2, dpf / 2), dpf)) * 1000 if abs else 2000
    den = 1000

    sp = "{pel:2,gpu:1,scale:{up:2,down:4}}"
    ap = "{gpu:1}"
    fp = "{rate:{num:%s,den:%s,abs:%s},algo:23}" % (num, den, str(abs).lower())

    ### fit the video size, video resolution multiple screen/monitor resolution
    r = max(vw/mw, vh/mh)
    if r > 1:
        def f(x, s=4): return round(x/r/s)*s
        clip = clip.resize.Spline36(width=f(vw), height=f(vh))

    ### convert bit
    if clip.format.id==vs.YUV420P8:
        clip8 = clip
    elif clip.format.id==vs.YUV420P10:
        # clip8 = clip.resize.Bilinear(format=vs.YUV420P8)
        clip8 = core.fmtc.bitdepth(clip, bits=8,dmode=0)
    else:
        # clip = clip.resize.Bilinear(format=vs.YUV420P10, dither_type="random")
        # clip8 = clip.resize.Bilinear(format=vs.YUV420P8)
        clip8 = core.fmtc.bitdepth(clip, bits=16,dmode=0)
        clip8 = core.fmtc.resample(clip8, css="420",kernel="spline36",interlaced=0, interlacedd=0)
        clip8 = core.fmtc.bitdepth(clip8, bits=8,dmode=0)

    ### svpflow read & add frame
    svps = core.svp1.Super(clip8, sp)
    r = svps["clip"], svps["data"]
    svpv = core.svp1.Analyse(*r, clip, ap)
    r = *r, svpv["clip"], svpv["data"]
    smooth = core.svp2.SmoothFps(clip, *r, fp, src=clip, fps=svf)

    if abs:
        smooth = core.std.AssumeFPS(smooth,fpsnum=smooth.fps_num,fpsden=smooth.fps_den)
    smooth.set_output()
