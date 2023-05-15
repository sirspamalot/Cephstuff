#!/usr/bin/env python
# check if there are orphean subvolume to delete on the ceph backend

import json
import sys
import subprocess

# Get all csi reference on k8s side for all cephfs pv
result = subprocess.run(
    ["oc", "get", "pv", "-o", "jsonpath={.items[*].spec.csi.volumeAttributes.subvolumeName}"],
    capture_output=True, text=True, check=True
)
k8s_ref = set(result.stdout.split())

# Get all csi reference on ceph side for all subvolume
result = subprocess.run(
    ["sh", "-c", "oc rsh -n openshift-storage `oc get po -n openshift-storage -l app=rook-ceph-tools -o name` sh -c 'ceph fs subvolume ls ocs-storagecluster-cephfilesystem csi --format json'"],
    capture_output=True, text=True, check=True
)
ceph_ref = set(list(map(lambda e: e['name'], json.loads(result.stdout))))

if not (ceph_ref - k8s_ref):
    sys.exit(0)

# I want ref present in ceph but not in k8s
print("Stale Subvolumes:")
for ref in (ceph_ref - k8s_ref):
    print("{}".format(ref))
sys.exit(1)
