import os
import sys
import glob
import shutil
import struct
import numpy as np
import cv2

def rotmat2qvec(R):
    tr = R[0, 0] + R[1, 1] + R[2, 2]
    if tr > 0:
        S = np.sqrt(tr + 1.0) * 2
        qw = 0.25 * S
        qx = (R[2, 1] - R[1, 2]) / S
        qy = (R[0, 2] - R[2, 0]) / S
        qz = (R[1, 0] - R[0, 1]) / S
    elif (R[0, 0] > R[1, 1]) and (R[0, 0] > R[2, 2]):
        S = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        qw = (R[2, 1] - R[1, 2]) / S
        qx = 0.25 * S
        qy = (R[0, 1] + R[1, 0]) / S
        qz = (R[0, 2] + R[2, 0]) / S
    elif R[1, 1] > R[2, 2]:
        S = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        qw = (R[0, 2] - R[2, 0]) / S
        qx = (R[0, 1] + R[1, 0]) / S
        qy = 0.25 * S
        qz = (R[1, 2] + R[2, 1]) / S
    else:
        S = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        qw = (R[1, 0] - R[0, 1]) / S
        qx = (R[0, 2] + R[2, 0]) / S
        qy = (R[1, 2] + R[2, 1]) / S
        qz = 0.25 * S
    q = np.array([qw, qx, qy, qz])
    if q[0] < 0:
        q = -q
    return q

def qvec2rotmat(qvec):
    return np.array([
        [1 - 2 * qvec[2]**2 - 2 * qvec[3]**2,
         2 * qvec[1] * qvec[2] - 2 * qvec[0] * qvec[3],
         2 * qvec[3] * qvec[1] + 2 * qvec[0] * qvec[2]],
        [2 * qvec[1] * qvec[2] + 2 * qvec[0] * qvec[3],
         1 - 2 * qvec[1]**2 - 2 * qvec[3]**2,
         2 * qvec[2] * qvec[3] - 2 * qvec[0] * qvec[1]],
        [2 * qvec[3] * qvec[1] - 2 * qvec[0] * qvec[2],
         2 * qvec[2] * qvec[3] + 2 * qvec[0] * qvec[1],
         1 - 2 * qvec[1]**2 - 2 * qvec[2]**2]])

def build_remap_coords(w_p, h_p, f, cx, cy, R_rel, w_eq, h_eq):
    x = np.arange(w_p, dtype=np.float32)
    y = np.arange(h_p, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    rx = (xx - cx) / f
    ry = (yy - cy) / f
    rz = np.ones_like(rx)
    norm = np.sqrt(rx**2 + ry**2 + rz**2)
    rays_cam = np.stack([rx/norm, ry/norm, rz/norm], axis=-1)
    
    r_sphere = rays_cam @ R_rel
    sx = r_sphere[..., 0]
    sy = r_sphere[..., 1]
    sz = r_sphere[..., 2]
    
    phi = np.arctan2(sx, sz)
    theta = np.arcsin(np.clip(-sy, -1.0, 1.0))
    
    map_x = ((phi / (2 * np.pi) + 0.5) * w_eq).astype(np.float32)
    map_y = ((0.5 - theta / np.pi) * h_eq).astype(np.float32)
    return map_x, map_y

def main():
    root = r'C:\gitprojects\working-dir-spheresfm'
    src_eq_images = os.path.join(root, 'images')
    src_eq_masks = os.path.join(root, 'masks')
    src_sphere_sparse = os.path.join(root, 'colmap', 'sparse', '0')
    src_cubic = os.path.join(root, 'colmap', 'sparse-cubic')
    src_cubic_images = os.path.join(src_cubic, 'images')
    src_cubic_masks = os.path.join(root, 'masks-cubic')
    src_cubic_points = os.path.join(src_cubic, 'sparse', '0', 'points3D.bin')
    
    dst_dir = os.path.join(root, 'colmap', 'sparse-cubic-angled')
    dst_images = os.path.join(dst_dir, 'images')
    dst_masks = os.path.join(dst_dir, 'masks')
    dst_sparse = os.path.join(dst_dir, 'sparse', '0')
    
    os.makedirs(dst_images, exist_ok=True)
    os.makedirs(dst_masks, exist_ok=True)
    os.makedirs(dst_sparse, exist_ok=True)
    
    print('Reading spherical image poses from', src_sphere_sparse)
    sphere_poses = {} # name -> (qvec, tvec)
    with open(os.path.join(src_sphere_sparse, 'images.bin'), 'rb') as f:
        num_images = struct.unpack('<Q', f.read(8))[0]
        for _ in range(num_images):
            img_id = struct.unpack('<I', f.read(4))[0]
            qw, qx, qy, qz = struct.unpack('<4d', f.read(32))
            tx, ty, tz = struct.unpack('<3d', f.read(24))
            cam_id = struct.unpack('<I', f.read(4))[0]
            name = []
            while True:
                ch = f.read(1)
                if ch == b'\x00': break
                name.append(ch.decode('latin1'))
            name = ''.join(name)
            num_pts = struct.unpack('<Q', f.read(8))[0]
            f.seek(num_pts * 24, 1)
            sphere_poses[name] = (np.array([qw, qx, qy, qz]), np.array([tx, ty, tz]))
            
    print(f'Found {len(sphere_poses)} spherical panorama poses.')
    
    R_yaw_0 = np.eye(3)
    R_yaw_90 = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], dtype=float)
    R_yaw_180 = np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]], dtype=float)
    R_yaw_270 = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], dtype=float)
    R_floor = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=float)
    
    c45 = np.cos(np.radians(45))
    s45 = np.sin(np.radians(45))
    R_pitch_up = np.array([[1, 0, 0], [0, c45, s45], [0, -s45, c45]])
    
    rel_rotations = [
        R_yaw_0,                  # 0: Front
        R_yaw_90,                 # 1: Right
        R_yaw_180,                # 2: Back
        R_yaw_270,                # 3: Left
        R_floor,                  # 4: Floor Down
        R_pitch_up @ R_yaw_0,     # 5: Front-Up
        R_pitch_up @ R_yaw_90,    # 6: Right-Up
        R_pitch_up @ R_yaw_180,   # 7: Back-Up
        R_pitch_up @ R_yaw_270,   # 8: Left-Up
    ]
    
    w_p, h_p = 1920, 1920
    f_p = 960.0
    cx, cy = 960.0, 960.0
    w_eq, h_eq = 7680, 3840
    
    print('Precomputing remap coordinate tables for 4 upward views...')
    angled_remap_tables = []
    for k in range(5, 9):
        map_x, map_y = build_remap_coords(w_p, h_p, f_p, cx, cy, rel_rotations[k], w_eq, h_eq)
        angled_remap_tables.append((map_x, map_y))
        
    sorted_pano_names = sorted(sphere_poses.keys())
    output_image_records = []
    current_img_id = 1
    
    total_panos = len(sorted_pano_names)
    print(f'Generating 9-view dataset for {total_panos} panoramas...')
    
    for p_idx, pano_name in enumerate(sorted_pano_names):
        base_name = os.path.splitext(pano_name)[0]
        q_sphere, t_sphere = sphere_poses[pano_name]
        R_sphere = qvec2rotmat(q_sphere)
        
        eq_img_path = os.path.join(src_eq_images, pano_name)
        eq_img = cv2.imread(eq_img_path)
        
        eq_mask_path = os.path.join(src_eq_masks, f'{pano_name}.png')
        if not os.path.exists(eq_mask_path):
            eq_mask_path = os.path.join(src_eq_masks, f'{base_name}.png')
        eq_mask = cv2.imread(eq_mask_path, cv2.IMREAD_GRAYSCALE) if os.path.exists(eq_mask_path) else None
        
        for k in range(9):
            R_rel = rel_rotations[k]
            R_cam = R_rel @ R_sphere
            t_cam = R_rel @ t_sphere
            q_cam = rotmat2qvec(R_cam)
            
            view_filename = f'{base_name}_perspective_{k:08d}.jpg'
            out_img_path = os.path.join(dst_images, view_filename)
            out_mask_path = os.path.join(dst_masks, view_filename)
            
            if k < 4:
                src_img = os.path.join(src_cubic_images, f'{base_name}_perspective_{k:08d}.jpg')
                src_msk = os.path.join(src_cubic_masks, f'{base_name}_perspective_{k:08d}.jpg')
                if os.path.exists(src_img):
                    shutil.copy2(src_img, out_img_path)
                else:
                    m_x, m_y = build_remap_coords(w_p, h_p, f_p, cx, cy, R_rel, w_eq, h_eq)
                    persp = cv2.remap(eq_img, m_x, m_y, cv2.INTER_LINEAR)
                    cv2.imwrite(out_img_path, persp, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                if os.path.exists(src_msk):
                    shutil.copy2(src_msk, out_mask_path)
                elif eq_mask is not None:
                    m_x, m_y = build_remap_coords(w_p, h_p, f_p, cx, cy, R_rel, w_eq, h_eq)
                    p_mask = cv2.remap(eq_mask, m_x, m_y, cv2.INTER_NEAREST)
                    cv2.imwrite(out_mask_path, p_mask)
            elif k == 4:
                src_img = os.path.join(src_cubic_images, f'{base_name}_perspective_00000005.jpg')
                src_msk = os.path.join(src_cubic_masks, f'{base_name}_perspective_00000005.jpg')
                if os.path.exists(src_img):
                    shutil.copy2(src_img, out_img_path)
                else:
                    m_x, m_y = build_remap_coords(w_p, h_p, f_p, cx, cy, R_rel, w_eq, h_eq)
                    persp = cv2.remap(eq_img, m_x, m_y, cv2.INTER_LINEAR)
                    cv2.imwrite(out_img_path, persp, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                if os.path.exists(src_msk):
                    shutil.copy2(src_msk, out_mask_path)
                elif eq_mask is not None:
                    m_x, m_y = build_remap_coords(w_p, h_p, f_p, cx, cy, R_rel, w_eq, h_eq)
                    p_mask = cv2.remap(eq_mask, m_x, m_y, cv2.INTER_NEAREST)
                    cv2.imwrite(out_mask_path, p_mask)
            else:
                m_x, m_y = angled_remap_tables[k - 5]
                persp = cv2.remap(eq_img, m_x, m_y, cv2.INTER_LINEAR)
                cv2.imwrite(out_img_path, persp, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                if eq_mask is not None:
                    p_mask = cv2.remap(eq_mask, m_x, m_y, cv2.INTER_NEAREST)
                    cv2.imwrite(out_mask_path, p_mask)
                else:
                    white_mask = np.full((h_p, w_p), 255, dtype=np.uint8)
                    cv2.imwrite(out_mask_path, white_mask)
                    
            output_image_records.append((current_img_id, q_cam, t_cam, 1, view_filename))
            current_img_id += 1
            
        if (p_idx + 1) % 25 == 0 or (p_idx + 1) == total_panos:
            print(f'[{p_idx+1}/{total_panos}] Finished {pano_name}...')
            
    print(f'Writing COLMAP cameras.bin and images.bin ({len(output_image_records)} images)...')
    
    with open(os.path.join(dst_sparse, 'cameras.bin'), 'wb') as f:
        f.write(struct.pack('<Q', 1))
        f.write(struct.pack('<iiQQ', 1, 0, 1920, 1920))
        f.write(struct.pack('<3d', 960.0, 960.0, 960.0))
        
    with open(os.path.join(dst_sparse, 'images.bin'), 'wb') as f:
        f.write(struct.pack('<Q', len(output_image_records)))
        for img_id, q_cam, t_cam, cam_id, filename in output_image_records:
            f.write(struct.pack('<I', img_id))
            f.write(struct.pack('<4d', *q_cam))
            f.write(struct.pack('<3d', *t_cam))
            f.write(struct.pack('<I', cam_id))
            f.write(filename.encode('latin1') + b'\x00')
            f.write(struct.pack('<Q', 0))
            
    print('Copying points3D.bin...')
    shutil.copy2(src_cubic_points, os.path.join(dst_sparse, 'points3D.bin'))
    
    print(f'Successfully generated 9-view dataset at: {dst_dir}')
    print(f'Total images: {len(output_image_records)}')
    print(f'Images directory: {dst_images}')
    print(f'Masks directory: {dst_masks}')
    print(f'Sparse model: {dst_sparse}')

if __name__ == '__main__':
    main()
