1. Check carefully which OSD is failed:

```bash
$ ceph osd tree down
```

2. Remove this OSD from Ceph:
```bash
$ ceph osd crush remove osd.<<ID>>
removed item id <<ID>> name 'osd.<<ID>>' from crush map
$ ceph osd rm osd.<<ID>>
removed osd.<<ID>>
$ ceph auth del osd.<<ID>>
updated
```

3. Search for the OSD deployment which is failed because of the failed OSD.
4. Get the ocs-deviceset-localblock pvc name from the mount inside the OSD pod. This is later needed to remove deviceset local block device.
5. Remove the failed OSD deployment, otherwise rook operator will cry you a river:
```bash
$ ceph osd tree down
```

6. Get the pv name corresponding to the pvc and the kernel device name of the OSD block device by checking pv:
```bash
$ oc get pvc | grep <<pvcNameFromStep4>>
$ oc get -o yaml pv local-pv-<<UID>> | grep "storage.openshift.com/device-name"
```
This kernel device name (sd<<ID>>) is needed in further clean up of block deviceand local-storage operator.

7. Go ahead by deleting the pvc of the ocs-deviceset and the coresponding pv (provided by local-storage operator):
```bash
$ oc delete pvc ocs-deviceset-localblock-<<NodeId>>-data-<<UID>>
$ oc delete pv local-pv-<<UID>>
```
If this delete isn't finishing, remove the finalizers.

8. On the storage node wipefs and remove pv mount point of local-storage operator:
```bash
$ wipefs /dev/sd<<ID>>
$ rm -r /var/lib/kubelet/plugins/kubernetes.io~local-volume/volumeDevices/local-pv-<<UID>>
$ ls -rtl /dev/disk/by-id/ | grep "sd<<ID>>"
$ rm -r /mnt/local-storage/localblock/scsi-<<SCSIID>>
```

9. Afterwards the local-storage operator should create a new local pv.
10. If the local pv exists, odf operator will take this pv by creating a new matching pvc.
11. Afterwards the rook operator will create a new prepare OSD job and afterwards a deployment to deploy the OSD pod for this pvc/new device.
