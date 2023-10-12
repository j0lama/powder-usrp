#!/usr/bin/python

"""This profile allows the allocation of resources for over-the-air
operation in POWDERs indoor over-the-air (OTA) lab.

A map of the lab's layout is here: [OTA Lab Diagram](https://gitlab.flux.utah.edu/powderrenewpublic/powder-deployment/-/raw/master/diagrams/ota-lab.png)

The OTA Lab has a number of X310 SDRs connected to two broadband antennas; one
on the TX/RX port, and the other on RX2 port of channel 0. Each X310 is paired
with a compute node (by default a Dell d430).

The OTA Lab also has a number of B210s SDRs paired with an Intel NUC
small form factor compute node. These B210s are connected to broadband
antennas, one on each of the "channel A" TX/RX and RX2 ports.

This profile uses a disk image with UHD pre-installed and clones/builds/installs
srsRAN 22.04. The source code can be found at `/var/tmp/srsran` on each node
after the startup scripts for the experiment have finished.

Resources needed to realize a basic srsRAN setup consisting of a UE, an eNodeB
and an EPC core network:

  * Spectrum for LTE FDD opperation (uplink and downlink).
  * A "nuc+b210" OTA lab compute/SDR pair (This will run the UE side.)
  * An "x310" OTA Lab SDR. (This will be the radio side of the eNodeB.)
  * A "d740" or "d430" compute node. (This will run both the eNodeB software and the EPC software.)

Instructions:

**IMPORTANT: You MUST adjust the configuration of srsRAN eNodeB and UE
components if you changed the frequency ranges in the profile parameters. Do so
BEFORE starting any srsRAN processes! Please see instructions further on.**

Startup scripts will still be running when your experiment becomes ready. Watch
the "Startup" column on the "List View" tab for your experiment and wait until
all of the compute nodes show "Finished" before proceeding.

The instructions included below assume the following hardware set was selected
when the profile was instantiated:

 * ota-nuc1; ota-x310-1; d740

#### To run the srsRAN software

**To run the EPC**

Open a terminal on the `ota-x310-1-comp` node in your experiment. (Go to
the "List View" in your experiment. If you have ssh keys and an ssh client
working in your setup you should be able to click on the black "ssh -p ..."
command to get a terminal. If ssh is not working in your setup, you can open a
browser shell by clicking on the Actions icon corresponding to the node and
selecting Shell from the dropdown menu.)

Start up the EPC:

    sudo srsepc
    
**To run the eNodeB**

Open another terminal on the `ota-x310-1-comp` node in your experiment.

Adjust the frequencies to use, if necessary (*MANDATORY* if you have changed these in the profile parameters):

  * Open `/etc/srsran/enb.conf`
  * Set `dl_freq` to the center frequency for the downlink channel you allocated
    * E.g., `dl_freq = 3590e6` if your downlink channel is 3580 - 3600 MHz
  * Set `ul_freq` to the center frequency for the uplink channel you allocated
    * E.g., `ul_freq = 3510e6` if your uplink channel is 3550 - 3570 MHz

Start up the eNodeB:

    sudo srsenb

**To run the UE**

Open a terminal on the `ota-nuc1-b210` node in your experiment.

Adjust the frequencies to use, if necessary (*MANDATORY* if you have changed these in the profile parameters):

  * Open `/etc/srsran/ue.conf`
  * Set `dl_freq` to the center frequency for the downlink channel you allocated
    * E.g., `dl_freq = 3590e6` if your downlink channel is 3580 - 3600 MHz
  * Set `ul_freq` to the center frequency for the uplink channel you allocated
    * E.g., `ul_freq = 3510e6` if your uplink channel is 3550 - 3570 MHz

Start up the UE:

    sudo srsue

Note that it may take a minute or two for the UE to find the eNB and
connect.  You will see an "RRC Connected" message in the srsue output
once connectivity has been established.

**Verify functionality**

Open another terminal on the `ota-nuc1-b210` node in your experiment.

Verify that the virtual network interface tun_srsue" has been created:

    ifconfig tun_srsue

Run ping to the SGi IP address via your RF link:
    
    ping 172.16.0.1

Killing/restarting the UE process will result in connectivity being interrupted/restored.

If you are using an ssh client with X11 set up, you can run the UE with the GUI
enabled to see a real time view of the signals received by the UE:

    sudo srsue --gui.enable 1

You may also want to try different physical resource block (PRB)
allocations (channel bandwidths), which can be adjusted in the
`/etc/srslte/enb.conf` file on the `ota-x310-1-comp` node.  Look for
the `n_prb` parameter.  Do not go over your declared up and downlink
bandwidths!  The profile requests 20 MHz for up and downlink channels by
default (up to 100 PRBs).

#### Troubleshooting

**No compatible RF-frontend found**

If srsenb fails with an error indicating "No compatible RF-frontend found",
you'll need to flash the appropriate firmware to the X310 and power-cycle it
using the portal UI. Run `uhd_usrp_probe` in a shell on the associated compute
node to get instructions for downloading and flashing the firmware. Use the
Action buttons in the List View tab of the UI to power cycle the appropriate
X310 after downloading and flashing the firmware. If srsue fails with a similar
error, try power-cycling the associated NUC.

**UE can't sync with eNB**

If you find that the UE cannot sync with the eNB, passing
`--expert.tx_amplitude 1.0` to srsue may help. You may have to
rerun srsue a few times to get it to sync.  You can also try adjusting
the `freq_offset` parameter in the `/etc/srslte/ue.conf` file on the
`ota-nuc1-b210` node. Try setting it to `0`, or other offsets between
-10000 and 10000.  It is set to -6000 by default, which seems to work
best in the OTA lab.

"""

import os

import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.emulab.pnext as pn
import geni.rspec.igext as ig
import geni.rspec.emulab.spectrum as spectrum


class GLOBALS:
    BIN_PATH = "/local/repository/bin"
    ETC_PATH = "/local/repository/etc"
    DEFAULT_SRSRAN_HASH = "release_22_04"
    SRSLTE_IMG = "urn:publicid:IDN+emulab.net+image+PowderTeam:U18LL-SRSLTE"
    MNGR_ID = "urn:publicid:IDN+emulab.net+authority+cm"
    SRS_DEPLOY_SCRIPT = os.path.join(BIN_PATH, "deploy-srs.sh")
    ULDEFLOFREQ = 3550.0
    ULDEFHIFREQ = 3570.0
    DLDEFLOFREQ = 3580.0
    DLDEFHIFREQ = 3600.0

def x310_node_pair(idx, x310_radio):
    radio_link = request.Link("radio-link-%d"%(idx))
    radio_link.bandwidth = 10*1000*1000

    node = request.RawPC("%s-comp"%(x310_radio.radio_name))
    node.hardware_type = params.x310_pair_nodetype
    node.disk_image = GLOBALS.SRSLTE_IMG
    node.component_manager_id = GLOBALS.MNGR_ID
    node.addService(rspec.Execute(shell="bash", command="/local/repository/bin/add-nat-and-ip-forwarding.sh"))
    node.addService(rspec.Execute(shell="bash", command="/local/repository/bin/tune-cpu.sh"))
    node.addService(rspec.Execute(shell="bash", command="/local/repository/bin/tune-sdr-iface.sh"))
    cmd = "{} {}".format(GLOBALS.SRS_DEPLOY_SCRIPT, GLOBALS.DEFAULT_SRSRAN_HASH)
    node.addService(rspec.Execute(shell="bash", command=cmd))

    node_radio_if = node.addInterface("usrp_if")
    node_radio_if.addAddress(rspec.IPv4Address("192.168.40.1",
                                               "255.255.255.0"))
    radio_link.addInterface(node_radio_if)

    radio = request.RawPC("%s-radio"%(x310_radio.radio_name))
    radio.component_id = x310_radio.radio_name
    radio.component_manager_id = "urn:publicid:IDN+emulab.net+authority+cm"
    radio_link.addNode(radio)

def b210_nuc_pair(idx, b210_node):
    b210_nuc_pair_node = request.RawPC("%s-b210" % b210_node.node_id)
    b210_nuc_pair_node.component_id = b210_node.node_id
    b210_nuc_pair_node.disk_image = GLOBALS.SRSLTE_IMG
    b210_nuc_pair_node.addService(rspec.Execute(shell="bash", command="/local/repository/bin/update-config-files.sh"))
    b210_nuc_pair_node.addService(rspec.Execute(shell="bash", command="/local/repository/bin/tune-cpu.sh"))
    cmd = "{} {}".format(GLOBALS.SRS_DEPLOY_SCRIPT, GLOBALS.DEFAULT_SRSRAN_HASH)
    b210_nuc_pair_node.addService(rspec.Execute(shell="bash", command=cmd))


node_type = [
    ("d740",
     "Emulab, d740"),
    ("d430",
     "Emulab, d430")
]

portal.context.defineParameter("x310_pair_nodetype",
                               "Type of compute node paired with the X310 Radios",
                               portal.ParameterType.STRING,
                               node_type[1],
                               node_type)

lab_x310_names = [
    "ota-x310-1",
    "ota-x310-2",
    "ota-x310-3",
    "ota-x310-4",
]

portal.context.defineStructParameter("x310_radios", "OTA Lab X310 Radios", [],
                                     multiValue=True,
                                     itemDefaultValue=
                                     {},
                                     min=0, max=None,
                                     members=[
                                        portal.Parameter(
                                             "radio_name",
                                             "OTA Lab X310",
                                             portal.ParameterType.STRING,
                                             lab_x310_names[0],
                                             lab_x310_names)
                                     ])

ota_b210_names = [
    "ota-nuc1",
    "ota-nuc2",
    "ota-nuc3",
    "ota-nuc4",
]

portal.context.defineStructParameter("b210_nodes", "OTA Lab B210 Radios", [],
                                     multiValue=True,
                                     min=0, max=None,
                                     members=[
                                         portal.Parameter(
                                             "node_id",
                                             "OTA Lab B210",
                                             portal.ParameterType.STRING,
                                             ota_b210_names[0],
                                             ota_b210_names)
                                     ],
                                    )

portal.context.defineParameter(
    "ul_freq_min",
    "Uplink Frequency Min",
    portal.ParameterType.BANDWIDTH,
    GLOBALS.ULDEFLOFREQ,
    longDescription="Values are rounded to the nearest kilohertz."
)
portal.context.defineParameter(
    "ul_freq_max",
    "Uplink Frequency Max",
    portal.ParameterType.BANDWIDTH,
    GLOBALS.ULDEFHIFREQ,
    longDescription="Values are rounded to the nearest kilohertz."
)
portal.context.defineParameter(
    "dl_freq_min",
    "Downlink Frequency Min",
    portal.ParameterType.BANDWIDTH,
    GLOBALS.DLDEFLOFREQ,
    longDescription="Values are rounded to the nearest kilohertz."
)
portal.context.defineParameter(
    "dl_freq_max",
    "Downlink Frequency Max",
    portal.ParameterType.BANDWIDTH,
    GLOBALS.DLDEFHIFREQ,
    longDescription="Values are rounded to the nearest kilohertz."
)

# Bind parameters
params = portal.context.bindParameters()

# Check frequency parameters.
if params.ul_freq_min < 3358 or params.ul_freq_min > 3600 \
   or params.ul_freq_max < 3358 or params.ul_freq_max > 3600:
    perr = portal.ParameterError("CBAND uplink frequencies must be between 3358 and 3600 MHz", ['ul_freq_min', 'ul_freq_max'])
    portal.context.reportError(perr)
if params.ul_freq_max - params.ul_freq_min < 1:
    perr = portal.ParameterError("Minimum and maximum frequencies must be separated by at least 1 MHz", ['ul_freq_min', 'ul_freq_max'])
    portal.context.reportError(perr)
if params.dl_freq_min < 3358 or params.dl_freq_min > 3600 \
   or params.dl_freq_max < 3358 or params.dl_freq_max > 3600:
    perr = portal.ParameterError("CBAND downlink frequencies must be between 3358 and 3600 MHz", ['dl_freq_min', 'dl_freq_max'])
    portal.context.reportError(perr)
if params.dl_freq_max - params.dl_freq_min < 1:
    perr = portal.ParameterError("Minimum and maximum frequencies must be separated by at least 1 MHz", ['dl_freq_min', 'dl_freq_max'])
    portal.context.reportError(perr)

# Now verify.
portal.context.verifyParameters()

# Lastly, request resources.
request = portal.context.makeRequestRSpec()

for i, x310_radio in enumerate(params.x310_radios):
    x310_node_pair(i, x310_radio)

for i, b210_node in enumerate(params.b210_nodes):
    b210_nuc_pair(i, b210_node)

request.requestSpectrum(params.ul_freq_min, params.ul_freq_max, 0)
request.requestSpectrum(params.dl_freq_min, params.dl_freq_max, 0)
    
portal.context.printRequestRSpec()
