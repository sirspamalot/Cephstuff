#!/usr/bin/env python
"""Module checks if there are orphan subvolumes on the ceph backend and deletes them"""

import json
import sys
import subprocess
import re

# Get all csi reference on k8s side for all cephfs pv
result = subprocess.run(
    ["oc", "get", "pv", "-o", "jsonpath={.items[*].spec.csi.volumeAttributes.subvolumeName}"],
    stdout=subprocess.PIPE, check=True
)
k8s_ref = set(result.stdout.decode("utf-8").split())
print("Found Subvolumes in K8S: "+str(len(k8s_ref)))
if not k8s_ref:
    sys.exit(1)

# Get all csi reference on ceph side for all subvolume
result = subprocess.run(
    ["sh", "-c", "oc rsh -n openshift-storage `oc get pod -n openshift-storage -l app=rook-ceph-tools -o name` sh -c 'ceph fs subvolume ls ocs-storagecluster-cephfilesystem csi --format json'"],
    stdout=subprocess.PIPE, check=True
)
ceph_ref = set(list(map(lambda e: e['name'], json.loads(result.stdout))))
print("Subvolumes with CSI reference in Ceph: "+str(len(ceph_ref)))
if not ceph_ref:
    sys.exit(1)

# Check whether difference is of the two lists is measurable
diff = ceph_ref - k8s_ref
print("Stale Subvolumes: "+str(len(diff)))
if not diff:
    sys.exit(1)

# I want ref present in ceph but not in k8s
print("Stale Subvolumes List:")
r = re.compile(r'^csi-vol-\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$')
for ref in diff:

    # Checking whether subvolume name is correct
    if r.match("{}".format(ref)) is None:
        print("{}".format(ref)+" is not a valid subvolume name, skipping")
        continue

    # Checking whether subvolume has snapshots
    result = subprocess.run(
        ["sh", "-c", "oc rsh -n openshift-storage `oc get pod -n openshift-storage -l app=rook-ceph-tools -o name` sh -c 'ceph fs subvolume snapshot ls ocs-storagecluster-cephfilesystem "+"{}".format(ref)+" csi'"],
        stdout=subprocess.PIPE, check=False
    )
    snap_ref = set(list(map(lambda e: e['name'], json.loads(result.stdout))))
    if snap_ref:
        print("{}".format(ref)+" is used by snapshot, skipping")
    else:
        print("{}".format(ref)+" will be deleted, is orphaned")
        #result = subprocess.run(
        #   ["sh", "-c", "oc rsh -n openshift-storage `oc get po -n openshift-storage -l app=rook-ceph-tools -o name` sh -c 'ceph fs subvolume rm ocs-storagecluster-cephfilesystem "+"{}".format(ref)+" csi'"],
        #     stdout=subprocess.PIPE, check=False
        #)
sys.exit(0)
