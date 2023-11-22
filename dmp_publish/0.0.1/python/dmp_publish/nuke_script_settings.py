import nuke

import os
import sys
import argparse
import traceback

import dmp_gather


def create_read_node(file_path):
    read_node = nuke.nodes.Read()
    read_node["file"].setValue(file_path)
    read_node["first"].setValue(1001)
    read_node["origfirst"].setValue(1001)
    read_node["last"].setValue(1001)
    read_node["origlast"].setValue(1001)
    read_node["raw"].setValue(True)

    return read_node


def create_copy_node(layer_name, connect_to):
    top_copy_node = nuke.nodes.Copy()
    top_copy_node.setInput(0, connect_to)
    top_copy_node.setInput(1, connect_to)

    to_red = "{}.red".format(layer_name)
    to_green = "{}.green".format(layer_name)
    to_blue = "{}.blue".format(layer_name)
    to_alpha = "{}.alpha".format(layer_name)

    top_copy_node["from0"].setValue("rgba.red")
    top_copy_node["from1"].setValue("rgba.green")
    top_copy_node["from2"].setValue("rgba.blue")
    top_copy_node["from3"].setValue("rgba.alpha")
    top_copy_node["to0"].setValue(to_red)
    top_copy_node["to1"].setValue(to_green)
    top_copy_node["to2"].setValue(to_blue)
    top_copy_node["to3"].setValue(to_alpha)

    return top_copy_node


def nuke_script_settings(layers, version=None, save_path=None):
    print("=========================================================")
    print("\nGathered Layers: \n{}".format(" ".join(layers)))
    print("\nBuilding Nuke Script using \n{}".format(" ".join(layers)))

    script_name = os.path.join(save_path, "NukeScript", "v{0}", "dmp_v{1}.nk").format(version, version)

    if os.path.exists(script_name):
        print("\nNuke Script Already Exists, removing and creating a new one")
        os.remove(os.path.dirname(script_name))
        os.remove(script_name)

    if not os.path.exists(os.path.dirname(script_name)):
        os.makedirs(os.path.dirname(script_name))

    nuke.scriptSaveAs(script_name, 1) # Second Argument '1' means always overwrite existing nuke script, '0' doesn't
    nuke.scriptOpen(script_name)

    all_reads = []
    all_merges = []

    for layer in layers:
        layer_name = layer.split(".")[0]
        layer_red = "{}.red".format(layer_name)
        layer_green = "{}.green".format(layer_name)
        layer_blue = "{}.blue".format(layer_name)
        layer_alpha = "{}.alpha".format(layer_name)
        nuke.Layer(layer_name, [layer_red, layer_green, layer_blue, layer_alpha])

    print("\nDMP Layering Info:\n")
    print(" {} ".format(layers[0]))

    top_node = create_read_node(os.path.join(save_path, layers[0]))
    top_copy_node = create_copy_node(layers[0].split(".")[0], top_node)
    top_copy_node.setXYpos(top_node.xpos(), top_node.ypos() + 100)
    all_reads.append(top_node)

    dmp_width = top_node.width()
    dmp_height = top_node.height()
    dmp_format = "{} {} DMP_RES_FORMAT".format(dmp_width, dmp_height)
    nuke.addFormat(dmp_format)

    root_node = nuke.Root()
    root_node["format"].setValue("DMP_RES_FORMAT")
    root_node["first_frame"].setValue(1001)
    root_node["last_frame"].setValue(1001)

    for index in range(len(layers)):
        try:
            child_index = index + 1
            print(" |")
            print(" |")
            print(" |")
            print("{}-----".format(layers[child_index]))

            child_read = create_read_node(os.path.join(save_path, layers[child_index]))
            merge_node = nuke.nodes.Merge2()
            merge_node["also_merge"].setValue("all")

            layer_copy_name = layers[child_index].split(".")[0]
            copy_node = create_copy_node(layer_copy_name, child_read)

            all_reads.append(child_read)
            all_merges.append(merge_node)

            if index == 0:
                merge_node.setInput(0, top_copy_node)
                merge_node.setXYpos(top_copy_node.xpos(), top_copy_node.ypos() + 200)
                child_read.setXYpos(merge_node.xpos() - 200, merge_node.ypos() - 200)
                copy_node.setXYpos(child_read.xpos(), child_read.ypos() + 100)
            else:
                current_merge_index = all_merges.index(merge_node)
                previous_merge_index = current_merge_index - 1
                previous_merge_node = all_merges[previous_merge_index]

                merge_node.setInput(0, previous_merge_node)
                merge_node.setXYpos(previous_merge_node.xpos(), previous_merge_node.ypos() + 200)
                child_read.setXYpos(merge_node.xpos() - 200, merge_node.ypos() - 200)
                copy_node.setXYpos(child_read.xpos(), child_read.ypos() + 100)

                merge_node.setInput(1, copy_node)

        except IndexError as e:

            for node in nuke.allNodes():
                node.setSelected(False)

            write_node = nuke.nodes.Write()
            write_node.setInput(0, all_merges[-1])
            write_node.setXYpos(all_merges[-1].xpos(), all_merges[-1].ypos() + 200)

            render_path = os.path.join(save_path, "NukeRender", "v{0}", "DMP_COMBINED_v{1}.####.exr").format(version,
            version)

            if os.path.exists(render_path):
                print("\nNuke Render Already Exists, removing and creating a new one")
                os.remove(render_path)
                os.remove(os.path.dirname(render_path))

            if not os.path.exists(os.path.dirname(render_path)):
                os.makedirs(os.path.dirname(render_path))

            write_node["file"].setValue(render_path)
            write_node["channels"].setValue("all")
            write_node["file_type"].setValue("exr")
            write_node["create_directories"].setValue(True)
            write_node["raw"].setValue(True)

            print("\nBuilding Nuke Script Completed Using all gathered layers")
            try:
                print("\nRendering EXR...")
                nuke.execute(write_node)
                nuke.scriptSave(script_name)
                nuke.scriptClose()
                print("\nRendering Completed...")
                print("\nProceeding to Publish!")
            except Exception as e:
                print("\nFailed to Render", e)
                print(traceback.format_exc())
                return


def parse_arguments():
    parser = argparse.ArgumentParser(description='Publish to shotgun.')
    parser.add_argument('-p', "--path", help='File to Publish')
    parser.add_argument('-v', "--version", help='version number')

    parsed_args = parser.parse_args()
    return parsed_args


if __name__ == "__main__":
    args = parse_arguments()
    dmp_data = dmp_gather.DMPGatherData(args.path)
    dmp_layers = dmp_data.layers()
    dmp_version = str(dmp_data.get_version()).zfill(3)

    if args.version == "":
        publish_version = dmp_version
    else:
        publish_version = args.version.zfill(3)

    nuke_script_settings(dmp_layers, save_path=args.path, version=publish_version)