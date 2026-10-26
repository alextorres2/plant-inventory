import { useEffect, useRef, useState } from 'react';
import { deletePlantPhoto, getPlantPhotos, uploadPlantPhoto } from '../services/plantApi';
import type { PlantPhoto } from '../types/PlantPhoto';
import './PlantPhotos.css';

type PlantPhotosProps = {
  plantId: number;
  canEdit: boolean;
  onPhotosChanged: () => Promise<void>;
};

function today(): string {
  const now = new Date();
  const localDate = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return localDate.toISOString().slice(0, 10);
}

function displayDate(value: string): string {
  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message.trim()) return error.message;
  if (typeof error === 'string' && error.trim()) return error;
  return fallback;
}

function PlantPhotos({ plantId, canEdit, onPhotosChanged }: PlantPhotosProps) {
  const [photos, setPhotos] = useState<PlantPhoto[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [dateTaken, setDateTaken] = useState(today);
  const [caption, setCaption] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingPhotoIds, setDeletingPhotoIds] = useState<number[]>([]);
  const uploadInProgress = useRef(false);
  const deletingIds = useRef(new Set<number>());
  const wasEditing = useRef(canEdit);
  const cameraInput = useRef<HTMLInputElement>(null);
  const libraryInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (wasEditing.current && !canEdit) {
      setError('');
      setSelectedFiles([]);
      setCaption('');
      setDateTaken(today());
    }
    wasEditing.current = canEdit;
  }, [canEdit]);

  useEffect(() => {
    let isCurrent = true;
    getPlantPhotos(plantId)
      .then((data) => {
        if (isCurrent) setPhotos(data);
      })
      .catch((caught: unknown) => {
        if (isCurrent) setError(errorMessage(caught, 'Unable to load plant photos.'));
      })
      .finally(() => {
        if (isCurrent) setIsLoading(false);
      });
    return () => {
      isCurrent = false;
    };
  }, [plantId]);

  function addFiles(fileList: FileList | null) {
    if (!fileList) return;
    setError('');
    setSelectedFiles((current) => [...current, ...Array.from(fileList)]);
  }

  async function handleUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (uploadInProgress.current || selectedFiles.length === 0) return;

    uploadInProgress.current = true;
    setIsUploading(true);
    setError('');
    const uploadedPhotos: PlantPhoto[] = [];
    const failedFiles: File[] = [];
    const failures: string[] = [];

    for (const file of selectedFiles) {
      try {
        uploadedPhotos.push(await uploadPlantPhoto(plantId, file, dateTaken, caption));
      } catch (caught: unknown) {
        failedFiles.push(file);
        failures.push(`${file.name}: ${errorMessage(caught, 'Upload failed.')}`);
      }
    }

    if (uploadedPhotos.length > 0) {
      setPhotos((current) =>
        [...current, ...uploadedPhotos].sort((a, b) =>
          b.dateTaken.localeCompare(a.dateTaken) || b.id - a.id,
        ),
      );
      try {
        await onPhotosChanged();
      } catch {
        failures.push('Photo uploaded, but the plant thumbnail could not be refreshed.');
      }
    }

    setSelectedFiles(failedFiles);
    setError(failures.join(' '));
    if (failedFiles.length === 0) {
      setCaption('');
      setDateTaken(today());
    }
    uploadInProgress.current = false;
    setIsUploading(false);
  }

  async function handleDelete(photo: PlantPhoto) {
    if (deletingIds.current.has(photo.id)) return;
    deletingIds.current.add(photo.id);
    setDeletingPhotoIds(Array.from(deletingIds.current));
    setError('');
    try {
      await deletePlantPhoto(plantId, photo.id);
      setPhotos((current) => current.filter((item) => item.id !== photo.id));
      await onPhotosChanged();
    } catch (caught: unknown) {
      setError(errorMessage(caught, 'Unable to delete this photo. Please try again.'));
    } finally {
      deletingIds.current.delete(photo.id);
      setDeletingPhotoIds(Array.from(deletingIds.current));
    }
  }

  return (
    <section className="plant-photos" aria-labelledby="plant-photos-heading">
      <h2 id="plant-photos-heading">Growth timeline</h2>
      {canEdit && <form className="photo-upload-form" onSubmit={handleUpload}>
        <div className="photo-picker-actions">
          <button type="button" onClick={() => cameraInput.current?.click()} disabled={isUploading}>
            Take a photo
          </button>
          <button type="button" className="secondary-button" onClick={() => libraryInput.current?.click()} disabled={isUploading}>
            Choose existing photos
          </button>
        </div>
        <input
          ref={cameraInput}
          className="visually-hidden"
          type="file"
          accept="image/*"
          capture="environment"
          aria-label="Take a plant photo"
          disabled={isUploading}
          onChange={(event) => {
            addFiles(event.target.files);
            event.target.value = '';
          }}
        />
        <input
          ref={libraryInput}
          className="visually-hidden"
          type="file"
          accept="image/jpeg,image/png,image/webp,image/heic,image/heif,image/avif,video/quicktime,.jpg,.jpeg,.png,.webp,.heic,.heif,.avif,.mov"
          multiple
          aria-label="Choose existing plant photos"
          disabled={isUploading}
          onChange={(event) => {
            addFiles(event.target.files);
            event.target.value = '';
          }}
        />
        {selectedFiles.length > 0 && (
          <div className="photo-upload-fields">
            <p className="selected-photo-count" aria-live="polite">
              {selectedFiles.length} {selectedFiles.length === 1 ? 'photo' : 'photos'} selected
            </p>
            {selectedFiles.some((file) =>
              file.name.toLowerCase().endsWith('.mov') || file.type.toLowerCase() === 'video/quicktime',
            ) && (
              <p className="photo-conversion-note">
                Live Photo videos are automatically converted to a still image; motion is not saved.
              </p>
            )}
            <label className="photo-form-field">
              Date taken
              <input
                type="date"
                value={dateTaken}
                onChange={(event) => setDateTaken(event.target.value)}
                disabled={isUploading}
                required
              />
            </label>
            <label className="photo-form-field">
              Caption (optional)
              <input
                type="text"
                value={caption}
                maxLength={1000}
                onChange={(event) => setCaption(event.target.value)}
                disabled={isUploading}
              />
            </label>
            <button type="submit" disabled={isUploading}>
              {isUploading ? 'Uploading photos…' : `Upload ${selectedFiles.length} ${selectedFiles.length === 1 ? 'photo' : 'photos'}`}
            </button>
          </div>
        )}
      </form>}

      {error && <p className="photo-error" role="alert">{error}</p>}
      {isLoading ? (
        <p className="photo-status" role="status">Loading photos…</p>
      ) : photos.length === 0 ? (
        <p className="photo-status">No photos yet. Add one to start this plant’s timeline.</p>
      ) : (
        <ol className="photo-timeline">
          {photos.map((photo) => (
            <li className="photo-timeline-item" key={photo.id}>
              <img src={photo.imageUrl} alt={photo.caption || `Plant photo from ${displayDate(photo.dateTaken)}`} />
              <div className="photo-timeline-meta">
                <time dateTime={photo.dateTaken}>{displayDate(photo.dateTaken)}</time>
                {photo.caption && <p>{photo.caption}</p>}
                {canEdit && (
                  <button
                    className="photo-delete-button"
                    type="button"
                    onClick={() => void handleDelete(photo)}
                    disabled={deletingPhotoIds.includes(photo.id) || isUploading}
                  >
                    {deletingPhotoIds.includes(photo.id) ? 'Deleting…' : 'Delete photo'}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

export default PlantPhotos;
