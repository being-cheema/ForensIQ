"""Measure an Autopsy case DB against ForensIQ ground-truth targets (no ForensIQ numbers are changed)."""
import sys, os, re, json, sqlite3, glob, collections
sys.path.insert(0, "/Users/cheema/ForensIQ")
os.chdir("/Users/cheema/ForensIQ")
import pandas as pd
import multimodel_eval as M

def fiq_paths(tag):
    df, raw, feats = M.build_features(M.IMAGES[tag]["art_dir"], tag)
    return df["path"].astype(str).reset_index(drop=True)

PFX = re.compile(r"^/img_[^/]+(/vol_vol\d+)?", re.I)
def strip(p): return PFX.sub("", p, count=1)

def analyze(tag, case_dir):
    con = sqlite3.connect(f"file:{case_dir}/autopsy.db?mode=ro", uri=True)
    q = lambda s, *a: con.execute(s, a).fetchall()
    out = {"case_dir": case_dir}
    out["tsk_files_total"] = q("select count(*) from tsk_files")[0][0]
    out["by_type"] = {str(k): v for k, v in q("select type,count(*) from tsk_files group by 1")}
    out["by_dir_type"] = {str(k): v for k, v in q("select dir_type,count(*) from tsk_files group by 1")}
    # regular files: meta_type=1 ; dir_type=5 = regular name entry; dir_flags 1=allocated 2=unallocated
    out["regular_files_meta1_all"] = q("select count(*) from tsk_files where meta_type=1")[0][0]
    out["regular_fs_files_alloc"] = q("select count(*) from tsk_files where meta_type=1 and dir_type=5 and (dir_flags&1)=1")[0][0]
    out["regular_fs_files_unalloc"] = q("select count(*) from tsk_files where meta_type=1 and dir_type=5 and (dir_flags&2)=2")[0][0]
    out["directories"] = q("select count(*) from tsk_files where meta_type=2")[0][0]
    out["derived_or_carved_files"] = q("select count(*) from tsk_files where type in (2,3,4,5)")[0][0]
    out["bytes_regular_files_allocated"] = q("select coalesce(sum(size),0) from tsk_files where meta_type=1 and dir_type=5 and (dir_flags&1)=1")[0][0]
    out["image_size_bytes"] = q("select coalesce(sum(size),0) from tsk_image_info")[0][0]
    out["datasource_count"] = q("select count(*) from data_source_info")[0][0]
    # artifacts
    types = q("""select t.type_name, t.display_name, t.category_type, count(*), count(distinct b.obj_id)
                 from blackboard_artifacts b join blackboard_artifact_types t on t.artifact_type_id=b.artifact_type_id
                 group by 1,2,3 order by 4 desc""")
    out["artifacts_by_type"] = [dict(type=t, display=d, category=c, artifacts=n, distinct_objs=o) for t, d, c, n, o in types]
    # artifacts attached to a file (tsk_files obj) vs data source/other content
    rows = q("""select b.artifact_id, t.type_name, b.obj_id, f.parent_path, f.name, f.meta_type, f.dir_type, f.type
                from blackboard_artifacts b join blackboard_artifact_types t on t.artifact_type_id=b.artifact_type_id
                left join tsk_files f on f.obj_id=b.obj_id""")
    df = pd.DataFrame(rows, columns=["aid", "atype", "obj", "pp", "name", "meta", "dirt", "ftype"])
    df["full"] = (df.pp.fillna("") + df.name.fillna("")).map(strip)
    out["artifacts_total"] = int(len(df))
    out["artifacts_on_files"] = int(df.name.notna().sum())
    # a "flag" = any artifact attached to a file object; separate: detection-type (not pure parsed activity)
    DETECT = {"TSK_INTERESTING_FILE_HIT", "TSK_INTERESTING_ITEM", "TSK_HASHSET_HIT", "TSK_EXT_MISMATCH_DETECTED",
              "TSK_ENCRYPTION_DETECTED", "TSK_ENCRYPTION_SUSPECTED", "TSK_KEYWORD_HIT", "TSK_YARA_HIT",
              "TSK_VERIFICATION_FAILED", "TSK_OBJECT_DETECTED", "TSK_USER_CONTENT_SUSPECTED"}
    on_file = df[df.name.notna()]
    out["flags_by_type_on_files"] = on_file.groupby("atype").aid.count().sort_values(ascending=False).to_dict()
    out["distinct_files_by_type"] = on_file.groupby("atype")["obj"].nunique().sort_values(ascending=False).to_dict()
    det = on_file[on_file.atype.isin(DETECT)]
    out["detection_flag_types"] = sorted(DETECT)
    out["distinct_files_flagged_detection"] = int(det.obj.nunique())
    out["distinct_files_flagged_any_artifact"] = int(on_file.obj.nunique())
    out["distinct_files_flagged_any_excluding_ds"] = int(on_file[on_file.meta == 1].obj.nunique())
    # explanations: verbatim attribute text per artifact type
    ex = {}
    for t in df.atype.unique():
        r = q("""select b.artifact_id, f.parent_path||f.name, a.attribute_type_id, at.display_name, a.value_text, a.value_int32, a.value_int64
                 from blackboard_artifacts b join blackboard_artifact_types ty on ty.artifact_type_id=b.artifact_type_id
                 left join tsk_files f on f.obj_id=b.obj_id
                 left join blackboard_attributes a on a.artifact_id=b.artifact_id
                 left join blackboard_attribute_types at on at.attribute_type_id=a.attribute_type_id
                 where ty.type_name=? and a.artifact_id in (select artifact_id from blackboard_artifacts b2 join blackboard_artifact_types t2 on t2.artifact_type_id=b2.artifact_type_id where t2.type_name=? limit 5)
                 order by b.artifact_id""", t, t)
        g = collections.OrderedDict()
        for aid, path, atid, dn, vt, v32, v64 in r:
            e = g.setdefault(aid, {"file": path, "attributes": {}})
            if dn is not None: e["attributes"][dn] = vt if vt not in (None, "") else (v32 if v32 not in (None, 0) else v64)
        ex[t] = list(g.values())[:5]
    out["explanation_examples"] = ex
    # target coverage
    fp = fiq_paths(tag)
    tg = M.IMAGES[tag]["targets"]
    tg = tg(fp) if callable(tg) else tg
    active, all_idx = M.match_targets(fp, tg)
    flagged_paths = pd.Series(sorted(set(on_file.full.str.strip())))
    flagged_det = pd.Series(sorted(set(det.full.str.strip())))
    def cover(fl):
        fl_low = set(fl.str.lower())
        fl_join = list(fl_low)
        hit_targets, hit_files = [], set()
        for t in active:
            th = False
            for i in t["idx"]:
                p = fp[i].lower()
                if p in fl_low:
                    hit_files.add(i); th = True
            if th: hit_targets.append(t["name"])
        return {"targets_caught": len(hit_targets), "targets_total": len(active),
                "target_files_caught": len(hit_files), "target_files_total": len(all_idx),
                "caught_names": hit_targets, "missed_names": [t["name"] for t in active if t["name"] not in hit_targets]}
    out["coverage_any_artifact_on_file"] = cover(flagged_paths)
    out["coverage_detection_types_only"] = cover(flagged_det)
    # path-normalisation sanity: share of ForensIQ target paths that exist in Autopsy's file list
    allp = set(strip(a + b).lower() for a, b in q("select parent_path, name from tsk_files where parent_path is not null"))
    out["target_files_present_in_autopsy_listing"] = sum(1 for i in all_idx if fp[i].lower() in allp)
    return out

if __name__ == "__main__":
    tag, case = sys.argv[1], sys.argv[2]
    r = analyze(tag, case)
    json.dump(r, open(f"/Users/cheema/ForensIQ/reports/autopsy_baseline/raw_{tag}.json", "w"), indent=1, default=str)
    print(json.dumps({k: r[k] for k in r if k not in ("explanation_examples", "artifacts_by_type")}, indent=1, default=str))
