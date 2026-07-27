import { extractErrorMessage } from './error-extractor';

describe('Error Extractor Utility', () => {
  const FALLBACK = 'Default error message.';

  it('returns fallback string when error is null or undefined', () => {
    expect(extractErrorMessage(null, FALLBACK)).toBe(FALLBACK);
    expect(extractErrorMessage(undefined, FALLBACK)).toBe(FALLBACK);
  });

  it('extracts custom backend ErrorResponseEnvelope message', () => {
    const mockHttpError = {
      error: {
        status: 'error',
        error: {
          code: 'ALBUM_NOT_FOUND',
          message: 'The requested album record does not exist.',
        },
      },
    };
    expect(extractErrorMessage(mockHttpError, FALLBACK)).toBe(
      'The requested album record does not exist.',
    );
  });

  it('extracts field validation message from custom details list', () => {
    const mockValidationError = {
      error: {
        status: 'error',
        error: {
          code: 'VALIDATION_FAILED',
          message: 'Payload invalid.',
          details: [{ field: 'title_original', msg: 'Field is required.' }],
        },
      },
    };
    expect(extractErrorMessage(mockValidationError, FALLBACK)).toBe('Payload invalid.');
  });

  it('falls back to Starlette detail string when custom envelope is absent', () => {
    const mockStarletteError = {
      error: { detail: 'Access token has expired.' },
    };
    expect(extractErrorMessage(mockStarletteError, FALLBACK)).toBe('Access token has expired.');
  });
});
