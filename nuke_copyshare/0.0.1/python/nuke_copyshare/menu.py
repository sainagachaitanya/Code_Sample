
import nuke
from CopyShare import CopyShare


menu = nuke.menu("Nuke")
copyshare_menu = menu.addMenu("Copy and Share")
copyshare_menu.addCommand("Refresh", "CopyShare.refresh()")
copyshare_menu.addCommand("Usage", "CopyShare.usage()")
copyshare_menu.addCommand("Copy Nodes", "CopyShare.copy_nodes()")
