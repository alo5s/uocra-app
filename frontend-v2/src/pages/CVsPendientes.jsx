import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { cvsAPI } from '../api';
import { useToastStore } from '../store/uiStore';
import { Card, CardBody, Button, Loader } from '../components/ui';

export default function CVsPendientes() {
  const navigate = useNavigate();
  const toast = useToastStore();
  const [cvs, setCvs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCVs();
  }, []);

  const fetchCVs = async () => {
    try {
      const res = await cvsAPI.getAll({ estado: 'pendiente', per_page: 100 });
      setCvs(res.data.items);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAprobar = async (id) => {
    if (!confirm('¿Aprobar este CV?')) return;
    try {
      await cvsAPI.aprobar(id);
      toast.success('CV aprobado');
      fetchCVs();
    } catch (error) {
      toast.error('Error al aprobar CV');
    }
  };

  const handleRechazar = async (id) => {
    if (!confirm('¿Rechazar y eliminar este CV?')) return;
    try {
      await cvsAPI.rechazar(id);
      toast.success('CV rechazado');
      fetchCVs();
    } catch (error) {
      toast.error('Error al rechazar CV');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-yellow-500">
        <i className="bi bi-clock text-2xl"></i>
        <h2 className="text-xl font-semibold mb-0">{cvs.length} CVs pendientes de revisión</h2>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <Loader />
        </div>
      ) : cvs.length === 0 ? (
        <Card>
          <CardBody className="text-center py-12">
            <div className="flex items-center justify-center mx-auto mb-4 rounded-full bg-gray-100 w-20 h-20">
              <i className="bi bi-check-circle text-5xl text-gray-400"></i>
            </div>
            <h4 className="text-gray-600">No hay CVs pendientes</h4>
          </CardBody>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {cvs.map(cv => (
            <Card key={cv.id}>
              <CardBody>
                <div className="flex justify-between items-start mb-3">
                  <h4 className="font-semibold mb-0">{cv.nombre || 'Sin nombre'}</h4>
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
                    Pendiente
                  </span>
                </div>
                
                <div className="mb-4 space-y-1 text-sm text-gray-600">
                  {cv.dni && (
                    <p className="mb-1">
                      <span className="font-medium text-gray-500">DNI:</span> {cv.dni}
                    </p>
                  )}
                  {cv.telefono && (
                    <p className="mb-1">
                      <span className="font-medium text-gray-500">Teléfono:</span> {cv.telefono}
                    </p>
                  )}
                  {cv.email && (
                    <p className="mb-1">
                      <span className="font-medium text-gray-500">Email:</span> {cv.email}
                    </p>
                  )}
                  {cv.oficios && (
                    <p className="mb-1">
                      <span className="font-medium text-gray-500">Oficios:</span> {cv.oficios}
                    </p>
                  )}
                  <p className="mb-0">
                    <span className="font-medium text-gray-500">Origen:</span> {cv.origen === 'qr' ? 'Código QR' : 'Web'}
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/cvs/ver/${cv.id}`)}
                  >
                    <i className="bi bi-eye"></i>
                    Ver
                  </Button>
                  <Button
                    variant="success"
                    size="sm"
                    onClick={() => handleAprobar(cv.id)}
                  >
                    <i className="bi bi-check-lg"></i>
                    Aprobar
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleRechazar(cv.id)}
                  >
                    <i className="bi bi-x-lg"></i>
                    Rechazar
                  </Button>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}